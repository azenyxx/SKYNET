"""M2 clarification oracle (E-10). Deterministic, bounded clarification of E-09 AWAITING_INFORMATION results.

Questions are generated ONLY from the ambiguity[] items that the E-09 parser derived under CNL-001; each names the
original byte span, the ambiguity code and the answer kinds it accepts. Answers are typed, bounded and accepted only
for requested questions and kinds:
  quantity          {value, unit, scale}  -> replaces the final quantity of a linear / precedence / reified statement
  unit_scale        {unit?, scale?}       -> supplies a variable declaration's MISSING unit and/or scale (no overrides)
  statement         {text}                -> full replacement CNL statement, same head keyword and same identifier
  declaration       {text}                -> CNL variable declaration for exactly the unresolved name (inserted)
  replace_reference {name}                -> replaces the unresolved name in that statement by an already declared variable
A round is atomic: any unsolicited, conflicting, malformed or identity-changing answer rejects the whole round and the
source stays unchanged. Applied answers are re-parsed by the unmodified E-09 parser; a result that becomes UNSUPPORTED or
INVALID is rejected. Nothing is guessed, defaulted or converted. Rounds, answers, answer size and transcript size are
bounded; exceeding them yields CLARIFICATION_EXHAUSTED. ABSTAINED_UNSUPPORTED inputs get no questions. The oracle grants
no authority and produces no trusted state; the transcript is a digest-chained lineage record."""
import re

from .canonical import canonical_bytes, digest, sha256_hex
from .m2_cnl import DOMAIN, EXPR, ID, REL, STMT, UINT, UNIT, parse_cnl

CLARIFY_VERSION = "e10.clarify.1"
LIMITS = {"max_answer_bytes": 512, "max_answers": 32, "max_rounds": 3, "max_transcript_bytes": 65536}
MAXV = 10 ** 9
QTY_TAIL = {
    "linear": re.compile(rf"(?P<prefix>constraint +{ID}: +{EXPR} +{REL})(?: +(?P<rest>.*?))? *(?P<end>\.)"),
    "precedence": re.compile(rf"(?P<prefix>constraint +{ID}: +{ID} +starts after +{ID} +by at least)(?: +(?P<rest>.*?))? *(?P<end>\.)"),
    "reified_linear": re.compile(rf"(?P<prefix>constraint +{ID}: +{ID} +(?:if and only if|implies) +\({EXPR} +{REL})(?: +(?P<rest>[^)]*?))? *(?P<end>\)\.)"),
}
VAR_PARTS = re.compile(rf"variable +(?P<id>{ID}) +has +domain +(?P<dom>{DOMAIN})(?: +unit +(?P<unit>{UNIT}))?(?: +scale +(?P<scale>{UINT}))? *\.")
TARGET = re.compile(rf"undeclared reference '({ID})'")
HEAD_ID = {"variable": re.compile(rf"variable +({ID})\b"), "constraint": re.compile(rf"constraint +({ID}):")}


def _kind(text):
    head = text.split(" ", 1)[0]
    if head == "constraint":
        for k, rx in QTY_TAIL.items():
            if rx.fullmatch(text):
                return k
    return head


def _accepts(code, kind, text):
    if code == "UNRESOLVED_SCOPE":
        return ["declaration", "replace_reference"]
    if code == "MISSING_UNIT_OR_SCALE" and kind == "variable" and VAR_PARTS.fullmatch(text):
        return ["statement", "unit_scale"]
    if kind in QTY_TAIL and code in ("MISSING_UNIT_OR_SCALE", "MISSING_REQUIRED_SLOT", "UNIT_MISMATCH"):
        return ["quantity", "statement"]
    return ["statement"]


def _questions(src, parse):
    qs, seen = [], set()
    for a in parse.get("ambiguity", []):
        text = src[a["span"]["start"]:a["span"]["end"]].decode("ascii")
        kind = _kind(text)
        t = TARGET.search(a.get("detail", "")) if a["code"] == "UNRESOLVED_SCOPE" else None
        q = {"accepts": _accepts(a["code"], kind, text), "code": a["code"], "question": a["question"], "span": a["span"],
             "statement_kind": kind, "target": t.group(1) if t else None}
        q["question_id"] = "q-" + digest(dict(q, source=parse["source_blob_digest"]))[7:23]
        if q["question_id"] not in seen:
            seen.add(q["question_id"])
            qs.append(q)
    return qs


def _strip(r):
    return {k: v for k, v in r.items() if k != "projection_bytes"}


def start(source, limits=LIMITS):
    src = bytes(source)
    r = parse_cnl(src)
    try:
        text = src.decode("utf-8")
    except UnicodeDecodeError:
        text = None
    return {"clarify_version": CLARIFY_VERSION, "limits": dict(limits), "original_source_digest": r["source_blob_digest"],
            "parse": r, "questions": _questions(src, r) if r["status"] == "AWAITING_INFORMATION" else [], "round": 0,
            "source": text, "status": r["status"], "transcript": []}


def _declared(src):
    return {m.group(1) for line in src.split(b"\n") for m in [STMT["variable"].fullmatch(line.rstrip(b"\r").decode("ascii", "replace")[:-1])] if m}


def _insert_pos(src):
    pos, last = 0, None
    for line in src.split(b"\n"):
        if line.startswith(b"variable ") or line.startswith(b"task "):
            last = (pos, pos + len(line))
        pos += len(line) + 1
    eol = b"\r\n" if src[last[1] - 1:last[1]] == b"\r" else b"\n"
    return last[1] + 1, eol


def _edit(q, a, text, src):
    """Returns ('replace', new_text) | ('insert', line_text) | raises ValueError(code)."""
    k = a.get("kind")
    if k == "quantity":
        v, u, s = a.get("value"), a.get("unit"), a.get("scale")
        if set(a) != {"kind", "question_id", "scale", "unit", "value"} or not isinstance(v, int) or isinstance(v, bool) \
                or abs(v) > MAXV or not isinstance(u, str) or not re.fullmatch(UNIT, u) or not isinstance(s, int) \
                or isinstance(s, bool) or not 0 <= s <= 9:
            raise ValueError("INVALID_ANSWER_VALUE")
        m = QTY_TAIL[q["statement_kind"]].fullmatch(text)
        return "replace", f"{m.group('prefix')} {v} {u}@{s}{m.group('end')}"
    if k == "unit_scale":
        if not set(a) <= {"kind", "question_id", "scale", "unit"}:
            raise ValueError("INVALID_ANSWER_VALUE")
        m = VAR_PARTS.fullmatch(text)
        out = {}
        for f, rx in (("unit", UNIT), ("scale", UINT)):
            have, give = m.group(f), a.get(f)
            if give is not None and (not re.fullmatch(rx, str(give)) or (f == "scale" and (isinstance(give, bool) or not isinstance(give, int)))):
                raise ValueError("INVALID_ANSWER_VALUE")
            if have is not None and give is not None and str(give) != have:
                raise ValueError("CONFLICTING_ANSWER")
            if have is None and give is None:
                raise ValueError("INCOMPLETE_ANSWER")
            out[f] = have if have is not None else str(give)
        return "replace", f"variable {m.group('id')} has domain {m.group('dom')} unit {out['unit']} scale {out['scale']}."
    t = a.get("text")
    if k in ("statement", "declaration"):
        if set(a) != {"kind", "question_id", "text"} or not isinstance(t, str) or not t.isascii() or not t.endswith(".") \
                or any(c in t for c in "\r\n\t"):
            raise ValueError("INVALID_ANSWER_SYNTAX")
        if k == "declaration":
            m = STMT["variable"].fullmatch(t[:-1])
            if not m:
                raise ValueError("INVALID_ANSWER_SYNTAX")
            if m.group("id") != q["target"]:
                raise ValueError("IDENTITY_CHANGED")
            return "insert", t
        head = text.split(" ", 1)[0]
        if t.split(" ", 1)[0] != head:
            raise ValueError("IDENTITY_CHANGED")
        if head in HEAD_ID:
            a0, a1 = HEAD_ID[head].match(text), HEAD_ID[head].match(t)
            if not a1 or (a0 and a0.group(1) != a1.group(1)):
                raise ValueError("IDENTITY_CHANGED")
        return "replace", t
    if k == "replace_reference":
        n = a.get("name")
        if set(a) != {"kind", "name", "question_id"} or not isinstance(n, str) or not re.fullmatch(ID, n) or n == q["target"]:
            raise ValueError("INVALID_ANSWER_VALUE")
        if n not in _declared(src):
            raise ValueError("REFERENCE_NOT_DECLARED")
        head = re.match(rf"(constraint +{ID}: +|objective +(?:minimize|maximize) +)", text)
        if not head:
            raise ValueError("INVALID_ANSWER_VALUE")
        body = re.sub(rf"(?<![A-Za-z0-9_-]){re.escape(q['target'])}(?![A-Za-z0-9_-])", n, text[head.end():])
        return "replace_ref", head.group(0) + body
    raise ValueError("ANSWER_KIND_NOT_REQUESTED")


def answer(session, answers):
    """One bounded, atomic clarification round. Returns a NEW session."""
    s = dict(session)
    lim = s["limits"]
    if s["status"] != "AWAITING_INFORMATION":
        return dict(s, last_round={"decision": "REJECTED", "rejections": [{"code": "SESSION_NOT_AWAITING", "index": None}]})
    # CP2 F-03: shape/type validation BEFORE any lookup; malformed answers are rejected atomically and leave the
    # source, round counter and transcript untouched.
    if not isinstance(answers, list) or any(not isinstance(a, dict) or not isinstance(a.get("question_id"), str)
                                            or not isinstance(a.get("kind"), str) for a in answers):
        bad = None if not isinstance(answers, list) else next(i for i, a in enumerate(answers) if not isinstance(a, dict)
                                                                 or not isinstance(a.get("question_id"), str)
                                                                 or not isinstance(a.get("kind"), str))
        return dict(s, last_round={"decision": "REJECTED", "rejections": [{"code": "INVALID_ANSWER_SHAPE", "index": bad}],
                                   "transcript_unchanged": True})
    src = s["source"].encode("utf-8")
    qmap = {q["question_id"]: q for q in s["questions"]}
    rej, chosen = [], {}
    if not isinstance(answers, list) or len(answers) > lim["max_answers"]:
        rej.append({"code": "TOO_MANY_ANSWERS", "index": None})
        answers = []
    for i, a in enumerate(answers):
        try:
            if not isinstance(a, dict) or len(canonical_bytes(a)) > lim["max_answer_bytes"]:
                raise ValueError("ANSWER_TOO_LARGE" if isinstance(a, dict) else "INVALID_ANSWER_SYNTAX")
        except ValueError as e:
            rej.append({"code": str(e), "index": i})
            continue
        except Exception:
            rej.append({"code": "INVALID_ANSWER_SYNTAX", "index": i})
            continue
        q = qmap.get(a.get("question_id"))
        if q is None:
            rej.append({"code": "UNSOLICITED_ANSWER", "index": i})
        elif a.get("kind") not in q["accepts"]:
            rej.append({"code": "ANSWER_KIND_NOT_REQUESTED", "index": i})
        elif q["question_id"] in chosen and canonical_bytes(chosen[q["question_id"]]) != canonical_bytes(a):
            rej.append({"code": "CONFLICTING_ANSWER", "index": i})
        else:
            chosen[q["question_id"]] = a
    edits, inserts = {}, []
    for qid in sorted(chosen):
        q, a = qmap[qid], chosen[qid]
        sp = (q["span"]["start"], q["span"]["end"])
        cur = edits.get(sp, ("none", src[sp[0]:sp[1]].decode("ascii")))
        try:
            op, val = _edit(q, a, cur[1] if cur[0] == "replace_ref" else src[sp[0]:sp[1]].decode("ascii"), src)
        except ValueError as e:
            rej.append({"code": str(e), "question_id": qid})
            continue
        if op == "insert":
            inserts.append(val)
        elif sp in edits and not (op == "replace_ref" and edits[sp][0] == "replace_ref"):
            rej.append({"code": "CONFLICTING_ANSWER", "question_id": qid})
        else:
            edits[sp] = (op, val)
    if not chosen and not rej:
        rej.append({"code": "NO_ANSWERS", "index": None})
    new_src, parse = src, None
    if not rej:
        for (st, en), (_, val) in sorted(edits.items(), reverse=True):
            new_src = new_src[:st] + val.encode("ascii") + new_src[en:]
        if inserts:
            pos, eol = _insert_pos(new_src)
            new_src = new_src[:pos] + b"".join(t.encode("ascii") + eol for t in sorted(inserts)) + new_src[pos:]
        parse = parse_cnl(new_src)
        if parse["status"] in ("ABSTAINED_UNSUPPORTED", "INVALID_INPUT", "RESOURCE_LIMIT"):
            rej.append({"code": "ANSWER_PRODUCED_" + parse["status"], "detail": parse.get("error", {}).get("code")})
    decision = "REJECTED" if rej else "APPLIED"
    entry = {"answers": [chosen[k] for k in sorted(chosen)], "decision": decision,
             "parent_digest": s["transcript"][-1]["entry_digest"] if s["transcript"] else None,
             "parse_status": parse["status"] if parse and not rej else None, "questions": sorted(qmap),
             "rejections": rej, "round": s["round"] + 1, "source_digest_after": "sha256:" + sha256_hex(new_src if not rej else src),
             "source_digest_before": "sha256:" + sha256_hex(src)}
    entry["entry_digest"] = digest(entry)
    s["transcript"] = s["transcript"] + [entry]
    s["round"] += 1
    s["last_round"] = {"decision": decision, "rejections": rej}
    if not rej:
        s["source"], s["parse"] = new_src.decode("ascii" if new_src.isascii() else "utf-8"), parse
        s["status"] = parse["status"]
        s["questions"] = _questions(new_src, parse) if parse["status"] == "AWAITING_INFORMATION" else []
    if s["status"] == "AWAITING_INFORMATION" and (s["round"] >= lim["max_rounds"] or
                                                  len(canonical_bytes(s["transcript"])) > lim["max_transcript_bytes"]):
        s["status"], s["questions"] = "CLARIFICATION_EXHAUSTED", []
    return s


def lineage(session):
    return {"clarified_source_digest": "sha256:" + sha256_hex(session["source"].encode("utf-8")) if session["source"] is not None else None,
            "original_source_digest": session["original_source_digest"], "rounds": session["round"], "status": session["status"],
            "transcript_head": session["transcript"][-1]["entry_digest"] if session["transcript"] else None}
