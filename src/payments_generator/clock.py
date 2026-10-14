"""Deterministic UTC clock."""

from __future__ import annotations

from datetime import datetime, timedelta, timezone

UTC = timezone.utc
PRODUCT_CUTOFF = datetime(2025, 1, 1, tzinfo=UTC)


def parse_utc(value: str) -> datetime:
    return datetime.fromisoformat(value.replace("Z", "+00:00")).astimezone(UTC)


class Clock:
    def __init__(self, start: datetime) -> None:
        if start.tzinfo is None:
            start = start.replace(tzinfo=UTC)
        self._t = start.astimezone(UTC)

    @property
    def now(self) -> datetime:
        return self._t

    def set(self, value: datetime | str) -> datetime:
        self._t = parse_utc(value) if isinstance(value, str) else value.astimezone(UTC)
        return self._t

    def tick(self, **delta: int) -> datetime:
        if not delta:
            delta = {"minutes": 15}
        self._t = self._t + timedelta(**delta)
        return self._t
