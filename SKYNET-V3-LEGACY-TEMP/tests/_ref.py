"""Independent reference semantics for fixtures, written directly against the
SKYSPEC source (does not import skynet_v3). Implements its own fixed-point
conversion, time-stepped cumulative, pairwise no_overlap and direct table/element/
reification semantics."""
import itertools
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
FIX = ROOT / "fixtures"
E01_NAMES = ["F1_linear_feasibility", "F2_linear_optimization", "F3_precedence_scheduling",
             "F4_cumulative_resource", "F5_combined_planning"]
E02_NAMES = ["F6_assignment_alldiff_element", "F7_table_reified_config", "F8_no_overlap_unit_policy"]
NAMES = E01_NAMES + E02_NAMES


def load(name):
    return json.loads((FIX / f"{name}.json").read_bytes())


def dom_values(v):
    d = v["domain"]
    return list(range(d["lb"], d["ub"] + 1)) if "lb" in d else list(d["values"])


def _policy(spec):
    return spec.get("unit_policy", {}).get("constant_rescale", "none")


def qv(spec, q, target_scale):
    if q["scale"] == target_scale:
        return q["value"]
    assert _policy(spec) == "exact_upscale" and q["scale"] < target_scale
    return q["value"] * 10 ** (target_scale - q["scale"])


def _scale(spec, var):
    return next(v["scale"] for v in spec["variables"] if v["id"] == var)


def _lin(spec, g, a):
    lhs = sum(t["coef"] * a[t["var"]] for t in g["terms"])
    r = qv(spec, g["rhs"], _scale(spec, g["terms"][0]["var"]))
    return {"le": lhs <= r, "ge": lhs >= r, "eq": lhs == r}[g["op"]]


def ref_eval(spec, a):
    for v in spec["variables"]:
        if a.get(v["id"]) not in dom_values(v):
            return False
    for c in spec["constraints"]:
        g, k = c["args"], c["kind"]
        if k == "linear":
            ok = _lin(spec, g, a)
        elif k == "reified_linear":
            h = _lin(spec, g["linear"], a)
            ok = (a[g["lit"]] == 0 or h) if g["mode"] == "implies" else ((a[g["lit"]] == 1) == h)
        elif k == "alldiff":
            ok = len({a[x] for x in g["vars"]}) == len(g["vars"])
        elif k == "precedence":
            ok = a[g["after"]] >= a[g["before"]] + qv(spec, g["lag"], _scale(spec, g["before"]))
        elif k == "cumulative":
            cap = g["capacity"]
            ts = [(a[t["start"]], qv(spec, t["duration"], _scale(spec, t["start"])), qv(spec, t["demand"], cap["scale"]))
                  for t in g["tasks"]]
            ok = all(sum(dm for s, d, dm in ts if s <= time < s + d) <= cap["value"]
                     for time in range(min(s for s, _, _ in ts), max(s + d for s, d, _ in ts) + 1))
        elif k == "no_overlap":
            iv = [(a[t["start"]], qv(spec, t["duration"], _scale(spec, t["start"]))) for t in g["tasks"]]
            ok = all(s1 + d1 <= s2 or s2 + d2 <= s1 for (s1, d1), (s2, d2) in itertools.combinations(iv, 2))
        elif k == "table":
            ok = [a[x] for x in g["vars"]] in g["tuples"]
        elif k == "element":
            i, arr = a[g["index"]], g["array"]
            ok = 0 <= i < len(arr["values"]) and a[g["target"]] == qv(
                spec, {"scale": arr["scale"], "unit": arr["unit"], "value": arr["values"][i]}, _scale(spec, g["target"]))
        else:
            ok = False
        if not ok:
            return False
    return True


def ref_obj(spec, a):
    o = spec.get("objective")
    return None if o is None else sum(t["coef"] * a[t["var"]] for t in o["terms"])


def _better(spec, val, best):
    return best is None or (val < best if spec["objective"]["sense"] == "minimize" else val > best)


def brute_force(spec, derived=None):
    """Exhaustive optimum; `derived` (makespan) is set to the max of its precedence lower bounds."""
    free = [v for v in spec["variables"] if v["id"] != derived]
    dv = next((v for v in spec["variables"] if v["id"] == derived), None)
    best = None
    for combo in itertools.product(*[dom_values(v) for v in free]):
        a = {v["id"]: x for v, x in zip(free, combo)}
        if dv is not None:
            lbs = [a[c["args"]["before"]] + qv(spec, c["args"]["lag"], dv["scale"]) for c in spec["constraints"]
                   if c["kind"] == "precedence" and c["args"]["after"] == derived]
            a[derived] = max([dom_values(dv)[0]] + lbs)
        if ref_eval(spec, a) and _better(spec, ref_obj(spec, a), best):
            best = ref_obj(spec, a)
    return best


def longest_path(spec, target):
    es = {v["id"]: v["domain"]["lb"] for v in spec["variables"]}
    for _ in range(len(es)):
        for c in spec["constraints"]:
            g = c["args"]
            es[g["after"]] = max(es[g["after"]], es[g["before"]] + g["lag"]["value"])
    return es[target]


def _f6(spec):
    ws = sorted(k[2:] for k in (v["id"] for v in spec["variables"]) if k.startswith("j_"))
    arrays = {c["args"]["index"]: c["args"]["array"]["values"] for c in spec["constraints"] if c["kind"] == "element"}
    best = None
    for perm in itertools.permutations(range(4)):
        a = {}
        for w, j in zip(ws, perm):
            a["j_" + w], a["c_" + w] = j, arrays["j_" + w][j]
        if ref_eval(spec, a) and _better(spec, ref_obj(spec, a), best):
            best = ref_obj(spec, a)
    return best


def _f7(spec):
    dv = {v["id"]: dom_values(v) for v in spec["variables"]}
    prices = next(c["args"]["array"]["values"] for c in spec["constraints"] if c["kind"] == "element")
    best = None
    for m, p, w, t, cost in itertools.product(dv["m"], dv["p"], dv["w"], dv["turbo"], prices):
        a = {"m": m, "p": p, "w": w, "turbo": t, "cost": cost}
        if ref_eval(spec, a) and _better(spec, ref_obj(spec, a), best):
            best = ref_obj(spec, a)
    return best


def expected_objective(name):
    spec = load(name)
    if name.startswith("F1"):
        return None
    if name.startswith("F2"):
        return brute_force(spec)
    if name.startswith("F3"):
        return longest_path(spec, "M")
    if name.startswith("F6"):
        return _f6(spec)
    if name.startswith("F7"):
        return _f7(spec)
    return brute_force(spec, derived="M")
