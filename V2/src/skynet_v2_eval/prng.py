"""Deterministic, platform-independent PRNG (SHA-256 counter mode). Not for cryptographic secrets."""
from __future__ import annotations

import hashlib


class DetRNG:
    def __init__(self, seed: bytes, label: str = ""):
        self._key = hashlib.sha256(b"SKYNET:v2:PRNG\x00" + label.encode() + b"\x00" + seed).digest()
        self._ctr, self._buf = 0, b""

    def _bytes(self, n: int) -> bytes:
        while len(self._buf) < n:
            self._buf += hashlib.sha256(self._key + self._ctr.to_bytes(8, "big")).digest()
            self._ctr += 1
        out, self._buf = self._buf[:n], self._buf[n:]
        return out

    def below(self, n: int) -> int:
        if n <= 0:
            raise ValueError("n must be positive")
        k = (n.bit_length() + 7) // 8 + 1
        limit = (256 ** k // n) * n
        while True:
            v = int.from_bytes(self._bytes(k), "big")
            if v < limit:
                return v % n

    def between(self, lo: int, hi: int) -> int:
        return lo + self.below(hi - lo + 1)

    def chance_q6(self, p_q6: int) -> bool:
        return self.below(1_000_000) < p_q6

    def shuffled(self, items: list) -> list:
        out = list(items)
        for i in range(len(out) - 1, 0, -1):
            j = self.below(i + 1)
            out[i], out[j] = out[j], out[i]
        return out
