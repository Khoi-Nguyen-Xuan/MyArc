"""Timing logs for the upload pipeline, to see which stage is slow.

Every timed block logs one line, e.g.

    [timing] CMPUT 201 · syllabus agent: 41.3s

and `StageTimer.summary()` gives one line per upload with all stages.
"""

from __future__ import annotations

import logging
import time
from collections.abc import Iterator
from contextlib import contextmanager

logger = logging.getLogger("app.timing")


@contextmanager
def log_duration(label: str) -> Iterator[None]:
    """Log how long the block took, even if it raised."""
    start = time.perf_counter()
    try:
        yield
    finally:
        logger.info("[timing] %s: %.1fs", label, time.perf_counter() - start)


class StageTimer:
    """Times the stages of one upload and remembers them for a summary line."""

    def __init__(self, name: str) -> None:
        self.name = name
        self._start = time.perf_counter()
        self._stages: dict[str, float] = {}

    @contextmanager
    def stage(self, stage: str) -> Iterator[None]:
        start = time.perf_counter()
        try:
            yield
        finally:
            elapsed = time.perf_counter() - start
            self._stages[stage] = elapsed
            logger.info("[timing] %s · %s: %.1fs", self.name, stage, elapsed)

    def summary(self) -> str:
        total = time.perf_counter() - self._start
        parts = " | ".join(f"{stage} {seconds:.1f}s" for stage, seconds in self._stages.items())
        return f"[timing] {self.name} TOTAL {total:.1f}s = {parts}"
