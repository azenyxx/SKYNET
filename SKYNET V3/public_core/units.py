"""Public integer quantity utility.

Provides explicit unit matching and exact integer upscaling with overflow checks.
Unit identifiers are opaque; implicit cross-unit conversion is not supported.
This standalone utility does not expose internal planning or data-model contracts.
"""
from .errors import invalid

POLICIES = ("exact_upscale", "none")
RESERVED_UNITS = ("bool", "index")


def conform(q, unit, scale, policy, path, max_abs):
    if q["unit"] != unit:
        raise invalid("UNIT_MISMATCH", path, "unit differs from target; cross-unit conversion is not permitted")
    if q["scale"] == scale:
        return {"scale": q["scale"], "unit": q["unit"], "value": q["value"]}, None
    if policy == "exact_upscale" and q["scale"] < scale:
        factor = 10 ** (scale - q["scale"])
        v = q["value"] * factor
        if abs(v) > max_abs:
            raise invalid("RESCALE_OVERFLOW", path, "exact upscaling would exceed the integer bound")
        out = {"scale": scale, "unit": unit, "value": v}
        return out, {"factor": factor, "from": {"scale": q["scale"], "unit": unit, "value": q["value"]},
                     "path": path, "to": out}
    raise invalid("UNIT_MISMATCH", path,
                  f"scale differs from target; implicit rescaling is forbidden (policy={policy})")
