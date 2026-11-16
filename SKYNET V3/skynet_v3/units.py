"""Unit/scale semantics (E-02).

physical_value = value x 10^(-scale); all values are integers. Units are opaque
identifiers: NO cross-unit conversion exists. Variables are never rescaled.

Policies (declared in source as unit_policy.constant_rescale):
  none          (default) constant quantities must match the target unit AND scale.
  exact_upscale constant quantities with the same unit and a LOWER scale may be
                converted exactly: value * 10^(target_scale - scale), overflow-checked.
                Downscaling is never performed. Every conversion is recorded in
                IR.source_mapping.conversions.
Reserved units: 'bool' (scale 0, domain within {0,1}); 'index' (scale 0, domain >= 0)."""
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
