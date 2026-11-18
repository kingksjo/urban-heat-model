"""Bounded polling helper for asynchronous FortyGuard jobs."""

from __future__ import annotations

import time
from dataclasses import dataclass, field
from typing import Any

from src.client import ApiResponse, FortyGuardClient

TERMINAL_STATUSES = {"completed", "failed", "error", "cancelled"}


@dataclass
class PollResult:
    """Outcome of polling an async activity ID."""

    activity_id: str
    final_status: str
    attempts: int
    total_elapsed_s: float
    transitions: list[tuple[int, str, float]] = field(default_factory=list)
    final_response: ApiResponse | None = None


def poll_activity(
    client: FortyGuardClient,
    activity_id: str,
    *,
    interval_s: float = 5.0,
    max_attempts: int = 24,
) -> PollResult:
    """Poll GET /v1/status/{activity_id} until terminal state or max_attempts."""
    start = time.perf_counter()
    transitions: list[tuple[int, str, float]] = []
    last_response: ApiResponse | None = None
    last_status = "unknown"

    for attempt in range(1, max_attempts + 1):
        resp = client.get_status(activity_id)
        last_response = resp
        elapsed = round(time.perf_counter() - start, 3)

        status_val = "unknown"
        if isinstance(resp.body, dict):
            data_obj = resp.body.get("data") if isinstance(resp.body.get("data"), dict) else {}
            raw_status = (
                resp.body.get("status")
                or resp.body.get("state")
                or data_obj.get("status")
                or data_obj.get("state")
            )
            if raw_status is not None:
                status_val = str(raw_status)

        transitions.append((attempt, status_val, elapsed))
        last_status = status_val

        if resp.status_code >= 400 or status_val.lower() in TERMINAL_STATUSES:
            return PollResult(
                activity_id=activity_id,
                final_status=last_status,
                attempts=attempt,
                total_elapsed_s=elapsed,
                transitions=transitions,
                final_response=last_response,
            )

        if attempt < max_attempts:
            time.sleep(interval_s)

    return PollResult(
        activity_id=activity_id,
        final_status=f"timeout ({last_status})",
        attempts=max_attempts,
        total_elapsed_s=round(time.perf_counter() - start, 3),
        transitions=transitions,
        final_response=last_response,
    )
