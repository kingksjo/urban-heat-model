"""Reusable REST client helpers for the FortyGuard Temperature API."""

from __future__ import annotations

import json
import os
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import requests
from dotenv import load_dotenv

DEFAULT_BASE_URL = "https://api.fortyguard.com"


@dataclass
class ApiResponse:
    """Structured capture of a single REST call for logging and inspection."""

    method: str
    url: str
    status_code: int
    latency_s: float
    content_type: str | None
    body: Any


def load_api_key(env_path: str | Path | None = None) -> str:
    """Load FORTYGUARD_API_KEY from environment or .env without exposing it."""
    load_dotenv(dotenv_path=env_path)
    api_key = os.getenv("FORTYGUARD_API_KEY", "").strip()
    if not api_key or api_key == "your_key_here":
        raise RuntimeError(
            "FORTYGUARD_API_KEY is missing or unset. Add your key to .env first."
        )
    return api_key


class FortyGuardClient:
    """Thin HTTP client wrapping FortyGuard REST v1 endpoints."""

    def __init__(
        self,
        api_key: str | None = None,
        base_url: str = DEFAULT_BASE_URL,
        timeout: float = 30.0,
    ) -> None:
        self._api_key = api_key or load_api_key()
        self.base_url = base_url.rstrip("/")
        self.timeout = timeout
        self._session = requests.Session()
        self._session.headers.update(
            {
                "api-key": self._api_key,
                "Content-Type": "application/json",
            }
        )

    def request(
        self,
        method: str,
        path: str,
        *,
        json_body: dict[str, Any] | None = None,
        params: dict[str, Any] | None = None,
        timeout: float | None = None,
        retries: int = 0,
        backoff_s: float = 5.0,
    ) -> ApiResponse:
        """Send a REST request and return status, latency, and parsed payload.

        `retries` re-sends only on gateway errors (502/503/504). Keep it at 0 for
        credit-consuming POSTs (heatmap, satellite, ...) to avoid double submission;
        use it for read-only calls (status polling, usage check).
        """
        url = f"{self.base_url}/{path.lstrip('/')}"
        for attempt in range(retries + 1):
            start = time.perf_counter()
            resp = self._session.request(
                method=method.upper(),
                url=url,
                json=json_body,
                params=params,
                timeout=timeout or self.timeout,
            )
            latency_s = round(time.perf_counter() - start, 3)
            if resp.status_code not in (502, 503, 504) or attempt == retries:
                break
            time.sleep(backoff_s * (attempt + 1))
        content_type = resp.headers.get("Content-Type")
        try:
            body: Any = resp.json()
        except ValueError:
            body = resp.text
        return ApiResponse(
            method=method.upper(),
            url=url,
            status_code=resp.status_code,
            latency_s=latency_s,
            content_type=content_type,
            body=body,
        )

    def fetch_api_key_usage(self) -> ApiResponse:
        """Query account plan and credit usage via POST /v1/system/fetch-api-key-usage."""
        return self.request(
            "POST",
            "/v1/system/fetch-api-key-usage",
            json_body={"api_key": self._api_key},
            retries=3,
        )

    def get_status(self, activity_id: str) -> ApiResponse:
        """Poll an async job via GET /v1/status/{activity_id}."""
        return self.request("GET", f"/v1/status/{activity_id}", retries=2)


SENSITIVE_KEYS = {
    "api_key",
    "api-key",
    "token",
    "access_token",
    "secret",
    "password",
    "subscription_id",
}


def sanitize_payload(data: Any) -> Any:
    """Recursively redact sensitive credential fields before logging or saving."""
    if isinstance(data, dict):
        return {
            k: ("[REDACTED]" if k.lower() in SENSITIVE_KEYS else sanitize_payload(v))
            for k, v in data.items()
        }
    if isinstance(data, list):
        return [sanitize_payload(item) for item in data]
    return data


def save_sanitized_json(data: Any, output_path: str | Path) -> Path:
    """Persist API output JSON safely with credential fields redacted."""
    path = Path(output_path)
    path.parent.mkdir(parents=True, exist_ok=True)
    cleaned = sanitize_payload(data)
    path.write_text(json.dumps(cleaned, indent=2, ensure_ascii=False), encoding="utf-8")
    return path
