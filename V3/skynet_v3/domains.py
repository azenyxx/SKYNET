"""Domain helpers over normalized domains {kind:interval,lb,ub} | {kind:set,values(sorted)}."""


def dmin(d):
    return d["lb"] if d["kind"] == "interval" else d["values"][0]


def dmax(d):
    return d["ub"] if d["kind"] == "interval" else d["values"][-1]


def contains(d, x):
    return d["lb"] <= x <= d["ub"] if d["kind"] == "interval" else x in d["values"]


def union_size(domains):
    """Size of the union of domains without expanding intervals."""
    segs = []
    for d in domains:
        if d["kind"] == "interval":
            segs.append((d["lb"], d["ub"]))
        else:
            segs.extend((v, v) for v in d["values"])
    segs.sort()
    total, cur = 0, None
    for lo, hi in segs:
        if cur is None or lo > cur[1] + 1:
            if cur is not None:
                total += cur[1] - cur[0] + 1
            cur = [lo, hi]
        else:
            cur[1] = max(cur[1], hi)
    if cur is not None:
        total += cur[1] - cur[0] + 1
    return total
