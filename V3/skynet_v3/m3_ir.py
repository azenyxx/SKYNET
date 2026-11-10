"""M3 ir - typed finite-domain IR v1.1 (E-02), full frozen v1 vocabulary.
Deterministic normalization: vars by id; constraints by cid; linear/objective terms
by var; alldiff vars sorted (set semantics); cumulative/no_overlap tasks sorted;
table tuples sorted lexicographically (set semantics; table var order preserved);
element array order preserved. Quantities are explicit {value,unit,scale},
normalized per unit_policy (units.py); every conversion is recorded in
source_mapping.conversions. Nothing is dropped, weakened or reinterpreted."""
from .canonical import digest
from .errors import unsupported
from .m1_ingest_formal import MAXV
from .units import conform

IR_VERSION = "1.1"


def compile_ir(spec: dict) -> dict:
    if spec.get("channel") != "F":
        raise unsupported("CHANNEL_NOT_IN_E01", "$.channel", "only channel F is supported")
    policy = spec.get("unit_policy", {}).get("constant_rescale", "none")
    ents = sorted(spec["entities"], key=lambda e: e["id"])
    src_index = {e["id"]: i for i, e in enumerate(spec["entities"])}
    vu = {e["id"]: (e["unit"], e["scale"]) for e in ents}
    variables = [{"domain": e["domain"], "id": e["id"], "index": i, "scale": e["scale"],
                  "type": e["kind"], "unit": e["unit"]} for i, e in enumerate(ents)]
    conversions = []

    def norm(q, target, cid, field):
        out, conv = conform(q, target[0], target[1], policy, field, MAXV)
        if conv:
            conv["cid"] = cid
            conversions.append(conv)
        return out

    def lin_body(a, cid, field):
        terms = sorted(a["terms"], key=lambda t: t["var"])
        return {"op": a["op"], "rhs": norm(a["rhs"], vu[terms[0]["var"]], cid, field + ".rhs"), "terms": terms}

    cons = []
    for c in sorted(spec["constraints"], key=lambda c: c["cid"]):
        k, a, cid = c["kind"], c["args"], c["cid"]
        if k == "linear":
            body = lin_body(a, cid, "args")
        elif k == "reified_linear":
            body = {"linear": lin_body(a["linear"], cid, "args.linear"), "lit": a["lit"], "mode": a["mode"]}
        elif k == "alldiff":
            body = {"vars": sorted(a["vars"])}
        elif k == "precedence":
            body = {"after": a["after"], "before": a["before"], "lag": norm(a["lag"], vu[a["before"]], cid, "args.lag")}
        elif k == "cumulative":
            cap = dict(a["capacity"])
            tasks = [{"demand": norm(t["demand"], (cap["unit"], cap["scale"]), cid, f"args.tasks[{i}].demand"),
                      "duration": norm(t["duration"], vu[t["start"]], cid, f"args.tasks[{i}].duration"),
                      "start": t["start"]} for i, t in enumerate(a["tasks"])]
            tasks.sort(key=lambda t: (t["start"], t["duration"]["value"], t["demand"]["value"]))
            body = {"capacity": cap, "tasks": tasks}
        elif k == "no_overlap":
            tasks = [{"duration": norm(t["duration"], vu[t["start"]], cid, f"args.tasks[{i}].duration"),
                      "start": t["start"]} for i, t in enumerate(a["tasks"])]
            tasks.sort(key=lambda t: (t["start"], t["duration"]["value"]))
            body = {"tasks": tasks}
        elif k == "table":
            body = {"tuples": sorted(list(t) for t in a["tuples"]), "vars": list(a["vars"])}
        elif k == "element":
            tgt = vu[a["target"]]
            arr = a["array"]
            vals = [norm({"scale": arr["scale"], "unit": arr["unit"], "value": v}, tgt, cid,
                         f"args.array.values[{i}]")["value"] for i, v in enumerate(arr["values"])]
            body = {"array": {"scale": tgt[1], "unit": tgt[0], "values": vals}, "index": a["index"],
                    "target": a["target"]}
        else:  # defense in depth; M1 already rejects
            raise unsupported("CONSTRAINT_KIND_NOT_IN_E01", "$.constraints", f"kind '{k}' not compilable")
        cons.append({"body": body, "cid": cid, "kind": k, "source_span": c["source_span"]})
    objective = None
    if spec["objectives"]:
        o = spec["objectives"][0]
        objective = {"sense": o["sense"], "terms": sorted(o["terms"], key=lambda t: t["var"])}
    source_mapping = {
        "blob_digest": spec["source_blob_digest"],
        "constraints": [{"cid": c["cid"], "source_span": c["source_span"]} for c in cons],
        "conversions": sorted(conversions, key=lambda x: (x["cid"], x["path"])),
        "variables": [{"id": v["id"], "source_index": src_index[v["id"]]} for v in variables],
    }
    ir = {"constraints": cons, "encoding": "INTERVAL", "hints": [], "ir_version": IR_VERSION,
          "objective": objective, "reformulations": [], "source_mapping": source_mapping,
          "spec_digest": spec["spec_digest"], "unit_policy": policy, "vars": variables}
    ir["ir_digest"] = digest(ir)
    return ir


def ir_body_digest(ir: dict) -> str:
    return digest({k: v for k, v in ir.items() if k != "ir_digest"})
