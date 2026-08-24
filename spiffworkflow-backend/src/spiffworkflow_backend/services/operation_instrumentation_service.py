from __future__ import annotations

import time
from collections.abc import Generator
from contextlib import contextmanager
from typing import Any


class OperationInstrumentation:
    """Reusable, failure-isolated timing for an application operation."""

    def __init__(self) -> None:
        self.started_at = time.perf_counter()
        self.phase_durations_ms: dict[str, float] = {}
        self.finished = False
        self.observability_failures = 0

    @contextmanager
    def phase(self, phase_name: str) -> Generator[None, None, None]:
        phase_started_at = time.perf_counter()
        try:
            yield
        finally:
            duration_seconds = time.perf_counter() - phase_started_at
            self.phase_durations_ms[phase_name] = round(duration_seconds * 1000, 3)
            try:
                self._record_phase(phase_name, duration_seconds)
            except Exception:
                # Instrumentation must never alter application behavior.
                self.observability_failures += 1

    def finish_operation(self, result: str, **fields: Any) -> None:
        if self.finished:
            return
        self.finished = True
        duration_seconds = time.perf_counter() - self.started_at
        try:
            self._record_completion(result, duration_seconds)
        except Exception:
            self.observability_failures += 1
        try:
            self._log_completion(result, duration_seconds, fields)
        except Exception:
            self.observability_failures += 1

    def _record_phase(self, phase_name: str, duration_seconds: float) -> None:
        pass

    def _record_completion(self, result: str, duration_seconds: float) -> None:
        pass

    def _log_completion(self, result: str, duration_seconds: float, fields: dict[str, Any]) -> None:
        pass
