from __future__ import annotations
from itertools import cycle


class KeyPool:
    """Cycles through a list of API keys so a caller can retry a failed request under the next key."""

    def __init__(self, keys: list[str]):
        deduped = list(dict.fromkeys(k for k in keys if k))
        if not deduped:
            raise ValueError("KeyPool needs at least one non-empty key")
        self.keys = deduped
        self._cycle = cycle(range(len(self.keys)))
        self._idx = next(self._cycle)

    @property
    def current(self) -> str:
        return self.keys[self._idx]

    def rotate(self) -> str:
        """Advance to the next key (wraps around) and return it."""
        self._idx = next(self._cycle)
        return self.current

    def __len__(self) -> int:
        return len(self.keys)
