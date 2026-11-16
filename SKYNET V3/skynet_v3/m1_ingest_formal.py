"""M1 ingest_formal - SKYSPEC v1, full frozen constraint vocabulary (E-02):
linear, reified_linear, alldiff, cumulative, precedence, no_overlap, table, element.
Fail-closed; first error in document order is raised; nothing is silently dropped.
The ProblemSpec mirrors the source (quantities as written); normalization is M3's job."""
import re

from .canonical import CanonicalError, canonical_bytes, digest, sha256_hex, strict_loads
from .domains import dmax, dmin
from .errors import invalid, unsupported
from .units import POLICIES, conform

SKYSPEC_VERSION = "1.0"
SPEC_VERSION = "1.0"
LIMITS = {
    "max_input_bytes": 1_048_576,
    "max_vars": 5000,
    "max_constraints": 5000,
    "max_terms": 1000,
    "max_tasks": 1000,
    "max_set_values": 10000,
    "max_abs_value": 10**9,
    "max_abs_coef": 10**6,
    "max_table_arity": 32,
    "max_tuples": 10000,
    "max_table_cells": 200_000,
    "max_element_array": 10000,
}
ID_RE = re.compile(r"[A-Za-z][A-Za-z0-9_-]{0,63}\Z")
UNIT_RE = re.compile(r"[a-z][a-z0-9_]{0,31}\Z")
MAX_SCALE = 9
SUPPORTED_KINDS = ("alldiff", "cumulative", "element", "linear", "no_overlap", "precedence", "reified_linear", "table")
V1_KINDS_NOT_IN_E01 = ()  # E-01 name retained; empty since E-02 supports the full v1 vocabulary
MAXV = LIMITS["max_abs_value"]


def _is_int(x):
    return isinstance(x, int) and not isinstance(x, bool)


def _safe(name):
    return name if isinstance(name, str) and ID_RE.match(name) else "<unprintable>"


def _keys(obj, path, required, optional=()):
    if not isinstance(obj, dict):
        raise invalid("OBJECT_EXPECTED", path, "object expected")
    for k in obj:
        if k not in required and k not in optional:
            raise invalid("UNKNOWN_FIELD", f"{path}.{_safe(k)}", "unknown field (fail-closed)")
    for k in required:
        if k not in obj:
            raise invalid("MISSING_FIELD", f"{path}.{k}", "required field missing")


def _list(x, path, lo, hi):
    if not isinstance(x, list):
        raise invalid("ARRAY_EXPECTED", path, "array expected")
    if len(x) < lo:
        raise invalid("ARRAY_TOO_SHORT", path, f"at least {lo} element(s) required")
    if len(x) > hi:
        raise invalid("LIMIT_EXCEEDED", path, f"at most {hi} elements permitted")
    return x


def _int(x, path, lo=None):
    if not _is_int(x):
        raise invalid("INTEGER_EXPECTED", path, "integer expected")
    if abs(x) > MAXV:
        raise invalid("VALUE_OUT_OF_RANGE", path, f"|value| must be <= {MAXV}")
    if lo is not None and x < lo:
        raise invalid("VALUE_BELOW_MINIMUM", path, f"value must be >= {lo}")
    return x


def _ident(x, path):
    if not isinstance(x, str) or not ID_RE.match(x):
        raise invalid("INVALID_IDENTIFIER", path, "identifier must match [A-Za-z][A-Za-z0-9_-]{0,63}")
    return x


def _unit(x, path):
    if not isinstance(x, str) or not UNIT_RE.match(x):
        raise invalid("INVALID_UNIT", path, "unit must match [a-z][a-z0-9_]{0,31}")
    return x


def _scale(x, path):
    if not _is_int(x) or not 0 <= x <= MAX_SCALE:
        raise invalid("INVALID_SCALE", path, f"scale must be an integer in [0,{MAX_SCALE}]")
    return x


def _quantity(q, path, nonneg=False):
    _keys(q, path, ("scale", "unit", "value"))
    return {"value": _int(q["value"], path + ".value", 0 if nonneg else None),
            "unit": _unit(q["unit"], path + ".unit"),
            "scale": _scale(q["scale"], path + ".scale")}


def _domain(d, path):
    if not isinstance(d, dict):
        raise invalid("INVALID_DOMAIN", path, "domain must be {lb,ub} or {values}")
    if set(d) == {"lb", "ub"}:
        lb, ub = _int(d["lb"], path + ".lb"), _int(d["ub"], path + ".ub")
        if lb > ub:
            raise invalid("EMPTY_DOMAIN", path, "lb > ub")
        return {"kind": "interval", "lb": lb, "ub": ub}
    if set(d) == {"values"}:
        vals = _list(d["values"], path + ".values", 1, LIMITS["max_set_values"])
        for i, v in enumerate(vals):
            _int(v, f"{path}.values[{i}]")
        if len(set(vals)) != len(vals):
            raise invalid("DUPLICATE_DOMAIN_VALUE", path, "domain values must be distinct")
        return {"kind": "set", "values": sorted(vals)}
    raise invalid("INVALID_DOMAIN", path, "domain must be exactly {lb,ub} or {values}")


class _Ctx:
    def __init__(self, policy):
        self.policy = policy
        self.vars = {}

    def ref(self, x, path):
        _ident(x, path)
        if x not in self.vars:
            raise invalid("UNDECLARED_VARIABLE", path, "reference to undeclared variable")
        return x

    def u(self, v):
        return self.vars[v]["unit"], self.vars[v]["scale"]

    def conform(self, q, target, path):
        conform(q, target[0], target[1], self.policy, path, MAXV)


def _terms(terms, path, ctx):
    _list(terms, path, 1, LIMITS["max_terms"])
    out, seen = [], set()
    for i, t in enumerate(terms):
        p = f"{path}[{i}]"
        _keys(t, p, ("coef", "var"))
        v = ctx.ref(t["var"], p + ".var")
        if v in seen:
            raise invalid("DUPLICATE_TERM_VARIABLE", p + ".var", "variable repeated in term list")
        seen.add(v)
        c = t["coef"]
        if not _is_int(c):
            raise invalid("INTEGER_EXPECTED", p + ".coef", "integer coefficient expected")
        if abs(c) > LIMITS["max_abs_coef"]:
            raise invalid("COEFFICIENT_OUT_OF_RANGE", p + ".coef", f"|coef| must be <= {LIMITS['max_abs_coef']}")
        out.append({"var": v, "coef": c})
    return out


def _same(ctx, vs, path, what):
    first = ctx.u(vs[0])
    for i, v in enumerate(vs):
        if ctx.u(v) != first:
            raise invalid("UNIT_MISMATCH", f"{path}[{i}]", f"{what} must share one unit and scale")
    return first


def _linear(a, path, ctx):
    _keys(a, path, ("op", "rhs", "terms"))
    if a["op"] not in ("eq", "ge", "le"):
        raise invalid("INVALID_OPERATOR", path + ".op", "op must be one of eq, ge, le")
    terms = _terms(a["terms"], path + ".terms", ctx)
    rhs = _quantity(a["rhs"], path + ".rhs")
    u = _same(ctx, [t["var"] for t in terms], path + ".terms", "variables of a linear constraint")
    ctx.conform(rhs, u, path + ".rhs")
    return {"op": a["op"], "rhs": rhs, "terms": terms}


def _reified_linear(a, path, ctx):
    _keys(a, path, ("linear", "lit", "mode"))
    lit = ctx.ref(a["lit"], path + ".lit")
    if ctx.vars[lit]["unit"] != "bool":
        raise invalid("REIFICATION_LITERAL_NOT_BOOL", path + ".lit", "reification literal must have unit 'bool'")
    if a["mode"] not in ("equiv", "implies"):
        raise invalid("INVALID_REIFICATION_MODE", path + ".mode", "mode must be equiv or implies")
    lin = _linear(a["linear"], path + ".linear", ctx)
    if any(t["var"] == lit for t in lin["terms"]):
        raise invalid("REIFICATION_SELF_REFERENCE", path + ".lit", "literal may not appear in its own linear term")
    return {"linear": lin, "lit": lit, "mode": a["mode"]}


def _alldiff(a, path, ctx):
    _keys(a, path, ("vars",))
    vs = _list(a["vars"], path + ".vars", 2, LIMITS["max_terms"])
    for i, v in enumerate(vs):
        ctx.ref(v, f"{path}.vars[{i}]")
    if len(set(vs)) != len(vs):
        raise invalid("DUPLICATE_ALLDIFF_VARIABLE", path + ".vars", "variables must be distinct")
    _same(ctx, vs, path + ".vars", "alldiff variables")
    return {"vars": list(vs)}


def _precedence(a, path, ctx):
    _keys(a, path, ("after", "before", "lag"))
    b = ctx.ref(a["before"], path + ".before")
    f = ctx.ref(a["after"], path + ".after")
    if b == f:
        raise invalid("SELF_PRECEDENCE", path, "before and after must differ")
    lag = _quantity(a["lag"], path + ".lag")
    if ctx.u(b) != ctx.u(f):
        raise invalid("UNIT_MISMATCH", path + ".after", "before and after must share one unit and scale")
    ctx.conform(lag, ctx.u(b), path + ".lag")
    return {"after": f, "before": b, "lag": lag}


def _timeline_tasks(tasks, path, ctx, with_demand, min_duration):
    out, timeline = [], None
    for i, t in enumerate(tasks):
        p = f"{path}[{i}]"
        _keys(t, p, ("demand", "duration", "start") if with_demand else ("duration", "start"))
        s = ctx.ref(t["start"], p + ".start")
        if timeline is None:
            timeline = ctx.u(s)
        elif ctx.u(s) != timeline:
            raise invalid("UNIT_MISMATCH", p + ".start", "task starts must share one unit/scale timeline")
        dur = _quantity(t["duration"], p + ".duration", nonneg=True)
        if dur["value"] < min_duration:
            raise invalid("ZERO_DURATION_NOT_PERMITTED", p + ".duration", f"duration must be >= {min_duration}")
        ctx.conform(dur, timeline, p + ".duration")
        rec = {"duration": dur, "start": s}
        if with_demand:
            rec["demand"] = _quantity(t["demand"], p + ".demand", nonneg=True)
        out.append(rec)
    return out


def _cumulative(a, path, ctx):
    _keys(a, path, ("capacity", "tasks"))
    cap = _quantity(a["capacity"], path + ".capacity", nonneg=True)
    tasks = _timeline_tasks(_list(a["tasks"], path + ".tasks", 1, LIMITS["max_tasks"]), path + ".tasks", ctx, True, 0)
    for i, t in enumerate(tasks):
        ctx.conform(t["demand"], (cap["unit"], cap["scale"]), f"{path}.tasks[{i}].demand")
    return {"capacity": cap, "tasks": tasks}


def _no_overlap(a, path, ctx):
    _keys(a, path, ("tasks",))
    return {"tasks": _timeline_tasks(_list(a["tasks"], path + ".tasks", 1, LIMITS["max_tasks"]),
                                     path + ".tasks", ctx, False, 1)}


def _table(a, path, ctx):
    _keys(a, path, ("tuples", "vars"))
    vs = _list(a["vars"], path + ".vars", 1, LIMITS["max_table_arity"])
    for i, v in enumerate(vs):
        ctx.ref(v, f"{path}.vars[{i}]")
    if len(set(vs)) != len(vs):
        raise invalid("DUPLICATE_TABLE_VARIABLE", path + ".vars", "variables must be distinct")
    tuples = _list(a["tuples"], path + ".tuples", 1, LIMITS["max_tuples"])
    if len(tuples) * len(vs) > LIMITS["max_table_cells"]:
        raise invalid("LIMIT_EXCEEDED", path + ".tuples", "table exceeds the cell limit")
    seen = set()
    for i, tup in enumerate(tuples):
        p = f"{path}.tuples[{i}]"
        if not isinstance(tup, list):
            raise invalid("ARRAY_EXPECTED", p, "tuple must be an array")
        if len(tup) != len(vs):
            raise invalid("TABLE_ARITY_MISMATCH", p, f"tuple arity {len(tup)} != {len(vs)}")
        for j, x in enumerate(tup):
            _int(x, f"{p}[{j}]")
        key = tuple(tup)
        if key in seen:
            raise invalid("DUPLICATE_TUPLE", p, "duplicate tuple")
        seen.add(key)
    return {"tuples": [list(t) for t in tuples], "vars": list(vs)}


def _element(a, path, ctx):
    _keys(a, path, ("array", "index", "target"))
    idx = ctx.ref(a["index"], path + ".index")
    tgt = ctx.ref(a["target"], path + ".target")
    if idx == tgt:
        raise invalid("ELEMENT_SELF_REFERENCE", path, "index and target must differ")
    if ctx.vars[idx]["unit"] != "index":
        raise invalid("ELEMENT_INDEX_NOT_INDEX_TYPED", path + ".index", "index variable must have unit 'index'")
    arr = a["array"]
    _keys(arr, path + ".array", ("scale", "unit", "values"))
    unit, scale = _unit(arr["unit"], path + ".array.unit"), _scale(arr["scale"], path + ".array.scale")
    vals = _list(arr["values"], path + ".array.values", 1, LIMITS["max_element_array"])
    for i, v in enumerate(vals):
        _int(v, f"{path}.array.values[{i}]")
        ctx.conform({"scale": scale, "unit": unit, "value": v}, ctx.u(tgt), f"{path}.array.values[{i}]")
    d = ctx.vars[idx]["domain"]
    if dmin(d) < 0 or dmax(d) > len(vals) - 1:
        raise invalid("ELEMENT_INDEX_OUT_OF_BOUNDS", path + ".index",
                      f"index domain must lie within [0,{len(vals) - 1}]")
    return {"array": {"scale": scale, "unit": unit, "values": list(vals)}, "index": idx, "target": tgt}


_ARGS = {"alldiff": _alldiff, "cumulative": _cumulative, "element": _element, "linear": _linear,
         "no_overlap": _no_overlap, "precedence": _precedence, "reified_linear": _reified_linear, "table": _table}


def try_task_id(raw: bytes):
    """Best-effort task_id for rejection evidence; never raises."""
    try:
        obj = strict_loads(raw)
        tid = obj.get("task_id") if isinstance(obj, dict) else None
        return tid if isinstance(tid, str) and ID_RE.match(tid) else "UNKNOWN"
    except Exception:
        return "UNKNOWN"


def ingest(raw: bytes) -> dict:
    """SKYSPEC v1 canonical JSON bytes -> ProblemSpec(channel=F)."""
    if not isinstance(raw, (bytes, bytearray)):
        raise invalid("BYTES_EXPECTED", "$", "raw bytes expected")
    if len(raw) > LIMITS["max_input_bytes"]:
        raise invalid("INPUT_TOO_LARGE", "$", f"input exceeds {LIMITS['max_input_bytes']} bytes")
    obj = strict_loads(raw)
    try:
        canon = canonical_bytes(obj)
    except CanonicalError as e:
        raise invalid("NONCANONICAL_VALUE", "$", str(e))
    if canon != bytes(raw):
        raise invalid("NONCANONICAL_INPUT", "$",
                      "input bytes must equal the canonical serialization (sorted keys, no whitespace, UTF-8, NFC, no trailing newline)")
    blob_digest = "sha256:" + sha256_hex(bytes(raw))
    _keys(obj, "$", ("constraints", "skyspec_version", "task_id", "variables"), ("objective", "unit_policy"))
    if obj["skyspec_version"] != SKYSPEC_VERSION:
        raise invalid("UNSUPPORTED_SPEC_VERSION", "$.skyspec_version", f"expected '{SKYSPEC_VERSION}'")
    task_id = _ident(obj["task_id"], "$.task_id")
    policy = "none"
    if "unit_policy" in obj:
        _keys(obj["unit_policy"], "$.unit_policy", ("constant_rescale",))
        policy = obj["unit_policy"]["constant_rescale"]
        if policy not in POLICIES:
            raise invalid("INVALID_UNIT_POLICY", "$.unit_policy.constant_rescale", "must be 'none' or 'exact_upscale'")
    ctx = _Ctx(policy)

    variables = _list(obj["variables"], "$.variables", 1, LIMITS["max_vars"])
    entities = []
    for i, v in enumerate(variables):
        p = f"$.variables[{i}]"
        _keys(v, p, ("domain", "id", "scale", "unit"))
        vid = _ident(v["id"], p + ".id")
        if vid in ctx.vars:
            raise invalid("DUPLICATE_VARIABLE", p + ".id", "variable declared twice")
        dom = _domain(v["domain"], p + ".domain")
        unit, scale = _unit(v["unit"], p + ".unit"), _scale(v["scale"], p + ".scale")
        kind = "int_var"
        if unit == "bool":
            if scale != 0 or dmin(dom) < 0 or dmax(dom) > 1:
                raise invalid("BOOL_DOMAIN_INVALID", p, "bool variables need scale 0 and a domain within {0,1}")
            kind = "bool_var"
        elif unit == "index":
            if scale != 0 or dmin(dom) < 0:
                raise invalid("INDEX_DOMAIN_INVALID", p, "index variables need scale 0 and a non-negative domain")
            kind = "index_var"
        ctx.vars[vid] = {"domain": dom, "scale": scale, "unit": unit}
        entities.append({"domain": dom, "id": vid, "kind": kind, "scale": scale, "unit": unit})

    constraints = _list(obj["constraints"], "$.constraints", 0, LIMITS["max_constraints"])
    marker = b'"constraints":['
    pos = canon.find(marker) + len(marker)
    out, cids = [], set()
    for i, c in enumerate(constraints):
        p = f"$.constraints[{i}]"
        _keys(c, p, ("args", "cid", "hard", "kind"))
        cid = _ident(c["cid"], p + ".cid")
        if cid in cids:
            raise invalid("DUPLICATE_CONSTRAINT_ID", p + ".cid", "constraint id declared twice")
        cids.add(cid)
        kind = c["kind"]
        if not isinstance(kind, str):
            raise invalid("INVALID_CONSTRAINT_KIND", p + ".kind", "kind must be a string")
        if kind not in SUPPORTED_KINDS:
            raise invalid("UNKNOWN_CONSTRAINT_KIND", p + ".kind", "unknown constraint kind")
        if not isinstance(c["hard"], bool):
            raise invalid("BOOLEAN_EXPECTED", p + ".hard", "boolean expected")
        if c["hard"] is not True:
            raise unsupported("SOFT_CONSTRAINT_NOT_IN_E01", p + ".hard", "soft constraints are not supported (E-01/E-02)")
        args = _ARGS[kind](c["args"], p + ".args", ctx)
        cb = canonical_bytes(c)
        start = canon.find(cb, pos)
        if start < 0:  # cannot happen for canonical input; fail closed
            raise invalid("SOURCE_SPAN_UNRESOLVED", p, "could not bind constraint to source span")
        pos = start + len(cb)
        out.append({"args": args, "cid": cid, "hard": True, "kind": kind,
                    "source_span": {"blob_digest": blob_digest, "end": pos, "start": start}})

    objectives = []
    o = obj.get("objective")
    if o is not None:
        _keys(o, "$.objective", ("sense", "terms"))
        if o["sense"] not in ("maximize", "minimize"):
            raise invalid("INVALID_OBJECTIVE_SENSE", "$.objective.sense", "sense must be maximize or minimize")
        objectives.append({"sense": o["sense"], "terms": _terms(o["terms"], "$.objective.terms", ctx)})

    obligations = [{"kind": "domain", "oid": "dom:" + e["id"], "ref": e["id"]} for e in entities]
    obligations += [{"kind": "constraint", "oid": "con:" + c["cid"], "ref": c["cid"]} for c in out]
    spec = {"ambiguity": [], "assumptions": [], "channel": "F", "constraints": out, "entities": entities,
            "objectives": objectives, "obligations": obligations, "questions": [],
            "source_blob_digest": blob_digest, "spec_version": SPEC_VERSION, "task_id": task_id}
    if "unit_policy" in obj:  # mirrors source; absent -> E-01 ProblemSpec shape unchanged
        spec["unit_policy"] = {"constant_rescale": policy}
    spec["spec_digest"] = digest(spec)
    return spec
