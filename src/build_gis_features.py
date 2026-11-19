"""Build the ~2,500+ tile Phase 4 ML dataset with free OpenStreetMap & geographic features.

Reads `data/raw/phase4_heatmaps/manifest.json`, extracts every 100m tile polygon and
FortyGuard `average_temperature` target, enriches each tile with:
1. Macro-geography: Haversine distance to LA coastline, distance to Downtown LA,
   and per-tile elevation (meters) from Open-Meteo Elevation API (batched & cached).
2. Urban form / land cover from OpenStreetMap (Overpass API, queried once per
   neighborhood bbox and cached under `data/raw/osm_cache/`):
   - building footprint % and count
   - total road length (m) and major arterial/highway length (m)
   - green/vegetation/park %, water %, industrial/commercial %, residential %, parking %

Outputs `data/processed/urban_heat_tiles.csv`.
"""

from __future__ import annotations

import json
import math
import time
from pathlib import Path
from typing import Any

import pandas as pd
import requests

MANIFEST_PATH = Path("data/raw/phase4_heatmaps/manifest.json")
OSM_CACHE_DIR = Path("data/raw/osm_cache")
ELEV_CACHE_PATH = Path("data/raw/elevation_cache.json")
OUTPUT_CSV = Path("data/processed/urban_heat_tiles.csv")

OVERPASS_URLS = [
    "https://overpass-api.de/api/interpreter",
    "https://overpass.private.coffee/api/interpreter",
    "https://maps.mail.ru/osm/tools/overpass/api/interpreter",
    "https://lz4.overpass-api.de/api/interpreter",
]
OVERPASS_HEADERS = {
    "User-Agent": "UrbanHeatPatternExplorer/1.0 (https://github.com/kingksjo/urban-heat-model)",
    "Accept": "application/json",
}
OPEN_METEO_ELEV_URL = "https://api.open-meteo.com/v1/elevation"

# Coarse-but-accurate Southern California coastline vertices (lon, lat) from Malibu to Long Beach
LA_COASTLINE_PTS: list[tuple[float, float]] = [
    (-118.680, 34.035), (-118.600, 34.038), (-118.550, 34.040),
    (-118.515, 34.027), (-118.498, 34.012), (-118.482, 33.992),
    (-118.462, 33.972), (-118.445, 33.952), (-118.432, 33.930),
    (-118.422, 33.905), (-118.414, 33.882), (-118.396, 33.858),
    (-118.392, 33.835), (-118.395, 33.810), (-118.410, 33.780),
    (-118.395, 33.745), (-118.355, 33.720), (-118.315, 33.708),
    (-118.285, 33.715), (-118.250, 33.728), (-118.215, 33.748),
    (-118.185, 33.758), (-118.150, 33.752), (-118.115, 33.740),
]
DTLA_COORD = (-118.2437, 34.0522)

GREEN_LEISURE = {"park", "garden", "golf_course", "nature_reserve", "playground", "pitch", "recreation_ground"}
GREEN_LANDUSE = {"grass", "forest", "meadow", "recreation_ground", "cemetery", "orchard", "vineyard", "village_green"}
GREEN_NATURAL = {"wood", "scrub", "grassland", "heath", "wetland", "tree_row"}
IND_COMM_LANDUSE = {"industrial", "commercial", "retail", "garages", "railway", "port"}
MAJOR_HIGHWAYS = {"motorway", "motorway_link", "trunk", "trunk_link", "primary", "primary_link", "secondary", "secondary_link"}


def haversine_km(lon1: float, lat1: float, lon2: float, lat2: float) -> float:
    r = 6371.0
    phi1, phi2 = math.radians(lat1), math.radians(lat2)
    dphi = math.radians(lat2 - lat1)
    dlmb = math.radians(lon2 - lon1)
    a = math.sin(dphi / 2.0) ** 2 + math.cos(phi1) * math.cos(phi2) * math.sin(dlmb / 2.0) ** 2
    return 2.0 * r * math.asin(math.sqrt(a))


def point_to_segment_km(lon: float, lat: float, a_lon: float, a_lat: float, b_lon: float, b_lat: float) -> float:
    # Local equirectangular projection around point for fast segment distance
    cos_lat = math.cos(math.radians(lat))
    kx = 111.320 * cos_lat
    ky = 110.574
    px, py = 0.0, 0.0
    ax, ay = (a_lon - lon) * kx, (a_lat - lat) * ky
    bx, by = (b_lon - lon) * kx, (b_lat - lat) * ky
    dx, dy = bx - ax, by - ay
    denom = dx * dx + dy * dy
    if denom <= 1e-12:
        return math.hypot(ax - px, ay - py)
    t = max(0.0, min(1.0, ((px - ax) * dx + (py - ay) * dy) / denom))
    projx, projy = ax + t * dx, ay + t * dy
    return math.hypot(projx - px, projy - py)


def dist_to_coast_km(lon: float, lat: float) -> float:
    best = float("inf")
    for i in range(len(LA_COASTLINE_PTS) - 1):
        a_lon, a_lat = LA_COASTLINE_PTS[i]
        b_lon, b_lat = LA_COASTLINE_PTS[i + 1]
        d = point_to_segment_km(lon, lat, a_lon, a_lat, b_lon, b_lat)
        if d < best:
            best = d
    return best


def extract_features_from_heatmap(raw_path: Path) -> list[dict[str, Any]]:
    data = json.loads(raw_path.read_text(encoding="utf-8"))
    if "poll" in data and isinstance(data["poll"], dict):
        data_node = (data["poll"].get("final_body") or {}).get("data") or {}
    elif "final_body" in data:
        data_node = (data["final_body"] or {}).get("data") or {}
    else:
        data_node = data.get("data") or {}
    return ((data_node.get("result") or {}).get("map_data") or {}).get("features") or []


def clip_polygon_to_rect(
    poly: list[tuple[float, float]], min_x: float, min_y: float, max_x: float, max_y: float
) -> list[tuple[float, float]]:
    """Sutherland-Hodgman polygon clipping against an axis-aligned rectangle."""
    def clip_edge(pts: list[tuple[float, float]], inside_fn, intersect_fn) -> list[tuple[float, float]]:
        if not pts:
            return []
        out: list[tuple[float, float]] = []
        prev = pts[-1]
        prev_in = inside_fn(prev)
        for curr in pts:
            curr_in = inside_fn(curr)
            if curr_in:
                if not prev_in:
                    out.append(intersect_fn(prev, curr))
                out.append(curr)
            elif prev_in:
                out.append(intersect_fn(prev, curr))
            prev, prev_in = curr, curr_in
        return out

    def ix_x(p1: tuple[float, float], p2: tuple[float, float], x: float) -> tuple[float, float]:
        dx = p2[0] - p1[0]
        t = (x - p1[0]) / dx if abs(dx) > 1e-12 else 0.0
        return (x, p1[1] + t * (p2[1] - p1[1]))

    def ix_y(p1: tuple[float, float], p2: tuple[float, float], y: float) -> tuple[float, float]:
        dy = p2[1] - p1[1]
        t = (y - p1[1]) / dy if abs(dy) > 1e-12 else 0.0
        return (p1[0] + t * (p2[0] - p1[0]), y)

    pts = poly
    pts = clip_edge(pts, lambda p: p[0] >= min_x, lambda a, b: ix_x(a, b, min_x))
    pts = clip_edge(pts, lambda p: p[0] <= max_x, lambda a, b: ix_x(a, b, max_x))
    pts = clip_edge(pts, lambda p: p[1] >= min_y, lambda a, b: ix_y(a, b, min_y))
    pts = clip_edge(pts, lambda p: p[1] <= max_y, lambda a, b: ix_y(a, b, max_y))
    return pts


def polygon_area_m2(pts: list[tuple[float, float]], ref_lat: float) -> float:
    if len(pts) < 3:
        return 0.0
    kx = 111320.0 * math.cos(math.radians(ref_lat))
    ky = 110574.0
    area = 0.0
    n = len(pts)
    for i in range(n):
        x1, y1 = pts[i][0] * kx, pts[i][1] * ky
        x2, y2 = pts[(i + 1) % n][0] * kx, pts[(i + 1) % n][1] * ky
        area += x1 * y2 - x2 * y1
    return abs(area) * 0.5


def clip_segment_to_rect(
    x1: float, y1: float, x2: float, y2: float, min_x: float, min_y: float, max_x: float, max_y: float
) -> tuple[float, float, float, float] | None:
    """Liang-Barsky line-segment clipping against an axis-aligned rectangle."""
    dx = x2 - x1
    dy = y2 - y1
    t0, t1 = 0.0, 1.0
    for p, q in (
        (-dx, x1 - min_x),
        (dx, max_x - x1),
        (-dy, y1 - min_y),
        (dy, max_y - y1),
    ):
        if abs(p) < 1e-12:
            if q < 0:
                return None
        else:
            r = q / p
            if p < 0:
                if r > t1:
                    return None
                if r > t0:
                    t0 = r
            else:
                if r < t0:
                    return None
                if r < t1:
                    t1 = r
    return (x1 + t0 * dx, y1 + t0 * dy, x1 + t1 * dx, y1 + t1 * dy)


def polyline_length_in_rect_m(
    coords: list[tuple[float, float]], min_x: float, min_y: float, max_x: float, max_y: float, ref_lat: float
) -> float:
    kx = 111320.0 * math.cos(math.radians(ref_lat))
    ky = 110574.0
    total = 0.0
    for i in range(len(coords) - 1):
        clipped = clip_segment_to_rect(
            coords[i][0], coords[i][1], coords[i + 1][0], coords[i + 1][1],
            min_x, min_y, max_x, max_y,
        )
        if clipped is not None:
            cx1, cy1, cx2, cy2 = clipped
            total += math.hypot((cx2 - cx1) * kx, (cy2 - cy1) * ky)
    return total


def fetch_osm_for_bbox(slug: str, bbox: list[float]) -> dict[str, Any]:
    OSM_CACHE_DIR.mkdir(parents=True, exist_ok=True)
    cache_path = OSM_CACHE_DIR / f"{slug}.json"
    if cache_path.exists():
        return json.loads(cache_path.read_text(encoding="utf-8"))

    # Pad bbox slightly (~150m) so edge buildings/roads aren't clipped out
    min_lon, min_lat, max_lon, max_lat = bbox
    pad = 0.0015
    s, w, n, e = min_lat - pad, min_lon - pad, max_lat + pad, max_lon + pad
    query = f"""
    [out:json][timeout:45];
    (
      way({s},{w},{n},{e})[~"^(building|highway|leisure|landuse|natural|waterway)$"~"."];
      way({s},{w},{n},{e})["amenity"="parking"];
    );
    out body;
    >;
    out skel qt;
    """
    last_err = None
    for attempt in range(10):
        url = OVERPASS_URLS[attempt % len(OVERPASS_URLS)]
        try:
            resp = requests.post(url, data={"data": query}, headers=OVERPASS_HEADERS, timeout=60)
            if resp.status_code == 200:
                payload = resp.json()
                cache_path.write_text(json.dumps(payload), encoding="utf-8")
                time.sleep(2.5)
                return payload
            last_err = f"HTTP {resp.status_code}: {resp.text[:150]}"
        except Exception as exc:
            last_err = str(exc)
        wait_s = min(20.0, 3.0 * (attempt + 1))
        print(f"    Overpass retry {attempt + 1}/10 ({url.split('/')[2]} -> {last_err[:60]}), waiting {wait_s:.0f}s...")
        time.sleep(wait_s)
    raise RuntimeError(f"Overpass failed for {slug}: {last_err}")


def parse_osm_elements(osm_json: dict[str, Any]) -> list[dict[str, Any]]:
    nodes: dict[int, tuple[float, float]] = {}
    for el in osm_json.get("elements", []):
        if el.get("type") == "node":
            nodes[el["id"]] = (float(el["lon"]), float(el["lat"]))

    ways: list[dict[str, Any]] = []
    for el in osm_json.get("elements", []):
        if el.get("type") != "way":
            continue
        tags = el.get("tags") or {}
        pts = [nodes[nid] for nid in el.get("nodes", []) if nid in nodes]
        if len(pts) < 2:
            continue
        xs = [p[0] for p in pts]
        ys = [p[1] for p in pts]
        is_closed = len(pts) >= 4 and pts[0] == pts[-1]
        ways.append({
            "tags": tags,
            "pts": pts,
            "is_closed": is_closed,
            "bbox": (min(xs), min(ys), max(xs), max(ys)),
        })
    return ways


def fetch_elevations_cached(coords: list[tuple[float, float]]) -> dict[str, float]:
    cache: dict[str, float] = {}
    if ELEV_CACHE_PATH.exists():
        cache = json.loads(ELEV_CACHE_PATH.read_text(encoding="utf-8"))

    missing: list[tuple[str, float, float]] = []
    for lat, lon in coords:
        key = f"{lat:.6f},{lon:.6f}"
        if key not in cache:
            missing.append((key, lat, lon))

    if missing:
        # Deduplicate rounded coordinates in case of duplicates
        print(f"Fetching elevation for {len(missing)} tiles in batches of 100...")
        for i in range(0, len(missing), 100):
            batch = missing[i : i + 100]
            lats = ",".join(f"{x[1]:.6f}" for x in batch)
            lons = ",".join(f"{x[2]:.6f}" for x in batch)
            for attempt in range(5):
                try:
                    resp = requests.get(
                        OPEN_METEO_ELEV_URL,
                        params={"latitude": lats, "longitude": lons},
                        timeout=30,
                    )
                    if resp.status_code == 200:
                        elevs = resp.json().get("elevation") or []
                        for (key, _, _), elev in zip(batch, elevs):
                            cache[key] = float(elev)
                        break
                    print(f"  Elevation batch {i} HTTP {resp.status_code}, retrying...")
                except Exception as exc:
                    print(f"  Warning: elevation batch {i} failed: {exc}")
                time.sleep(2.0 * (attempt + 1))
            time.sleep(0.8)
            ELEV_CACHE_PATH.write_text(json.dumps(cache), encoding="utf-8")
    return cache


def main() -> None:
    manifest = json.loads(MANIFEST_PATH.read_text(encoding="utf-8"))
    neighborhoods = manifest["neighborhoods"]
    print(f"Loaded manifest: {len(neighborhoods)} neighborhoods, {manifest['total_tiles']} expected tiles.")

    rows: list[dict[str, Any]] = []
    elev_coords: list[tuple[float, float]] = []

    for idx, nb in enumerate(neighborhoods, start=1):
        slug = nb["slug"]
        raw_path = Path(nb["file_path"])
        features = extract_features_from_heatmap(raw_path)
        print(f"[{idx}/{len(neighborhoods)}] {slug}: {len(features)} tiles — loading OSM...")
        osm_json = fetch_osm_for_bbox(slug, nb["bbox"])
        ways = parse_osm_elements(osm_json)

        for feat in features:
            props = feat.get("properties") or {}
            ring = ((feat.get("geometry") or {}).get("coordinates") or [[]])[0]
            if not ring:
                continue
            lons = [float(p[0]) for p in ring]
            lats = [float(p[1]) for p in ring]
            min_x, max_x = min(lons), max(lons)
            min_y, max_y = min(lats), max(lats)
            c_lon = (min_x + max_x) * 0.5
            c_lat = (min_y + max_y) * 0.5
            tile_area = polygon_area_m2(
                [(min_x, min_y), (max_x, min_y), (max_x, max_y), (min_x, max_y)], c_lat
            )
            if tile_area <= 0:
                continue

            bldg_area = 0.0
            bldg_count = 0
            green_area = 0.0
            water_area = 0.0
            ind_area = 0.0
            res_area = 0.0
            park_area = 0.0
            road_m = 0.0
            major_road_m = 0.0

            for w in ways:
                wx0, wy0, wx1, wy1 = w["bbox"]
                if wx1 < min_x or wx0 > max_x or wy1 < min_y or wy0 > max_y:
                    continue
                tags = w["tags"]
                pts = w["pts"]

                if "highway" in tags:
                    seg_len = polyline_length_in_rect_m(pts, min_x, min_y, max_x, max_y, c_lat)
                    road_m += seg_len
                    if tags["highway"] in MAJOR_HIGHWAYS:
                        major_road_m += seg_len

                if not w["is_closed"]:
                    continue

                clipped = clip_polygon_to_rect(pts[:-1], min_x, min_y, max_x, max_y)
                if len(clipped) < 3:
                    continue
                area = polygon_area_m2(clipped, c_lat)
                if area <= 0.1:
                    continue

                if "building" in tags:
                    bldg_area += area
                    bldg_count += 1
                if (
                    tags.get("leisure") in GREEN_LEISURE
                    or tags.get("landuse") in GREEN_LANDUSE
                    or tags.get("natural") in GREEN_NATURAL
                ):
                    green_area += area
                if tags.get("natural") == "water" or tags.get("landuse") == "reservoir":
                    water_area += area
                if tags.get("landuse") in IND_COMM_LANDUSE or "aeroway" in tags:
                    ind_area += area
                if tags.get("landuse") == "residential":
                    res_area += area
                if tags.get("amenity") == "parking":
                    park_area += area

            elev_coords.append((c_lat, c_lon))
            rows.append({
                "tile_uid": f"{slug}_{props.get('tile_id')}",
                "neighborhood": slug,
                "neighborhood_name": nb["name"],
                "zone": nb["zone"],
                "source": nb["source"],
                "tile_id": props.get("tile_id"),
                "centroid_lat": round(c_lat, 6),
                "centroid_lon": round(c_lon, 6),
                "tile_area_m2": round(tile_area, 2),
                "average_temperature": float(props["average_temperature"]),
                "min_temperature": float(props["min_temperature"]),
                "max_temperature": float(props["max_temperature"]),
                "dist_to_coast_km": round(dist_to_coast_km(c_lon, c_lat), 3),
                "dist_to_dtla_km": round(haversine_km(c_lon, c_lat, DTLA_COORD[0], DTLA_COORD[1]), 3),
                "osm_building_pct": round(min(100.0, 100.0 * bldg_area / tile_area), 3),
                "osm_building_count": bldg_count,
                "osm_road_length_m": round(road_m, 2),
                "osm_major_road_m": round(major_road_m, 2),
                "osm_green_pct": round(min(100.0, 100.0 * green_area / tile_area), 3),
                "osm_water_pct": round(min(100.0, 100.0 * water_area / tile_area), 3),
                "osm_industrial_comm_pct": round(min(100.0, 100.0 * ind_area / tile_area), 3),
                "osm_residential_pct": round(min(100.0, 100.0 * res_area / tile_area), 3),
                "osm_parking_pct": round(min(100.0, 100.0 * park_area / tile_area), 3),
            })

    elev_map = fetch_elevations_cached(elev_coords)
    for r in rows:
        key = f"{r['centroid_lat']:.6f},{r['centroid_lon']:.6f}"
        r["elevation_m"] = elev_map.get(key)

    df = pd.DataFrame(rows)
    OUTPUT_CSV.parent.mkdir(parents=True, exist_ok=True)
    df.to_csv(OUTPUT_CSV, index=False)
    print(f"\nSaved {len(df)} rows x {len(df.columns)} columns to {OUTPUT_CSV}")
    print(df[["average_temperature", "dist_to_coast_km", "elevation_m", "osm_building_pct", "osm_road_length_m", "osm_green_pct"]].describe().round(2))


if __name__ == "__main__":
    main()
