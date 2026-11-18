"""Independent educational utilities for paired binary research outcomes.

Public demonstration only. Not imported from SKYNET private P2/P1 code.
Standard library, Python 3.9+; no input/output or external dependencies.
"""
from math import comb, sqrt


def paired_table(baseline, candidate):
    """Return both_pass, candidate_only, baseline_only, both_fail.

    Mappings must contain exactly the same unique task keys; values must be bool.
    """
    if not isinstance(baseline, dict) or not isinstance(candidate, dict):
        raise TypeError("inputs must be task-id dictionaries")
    if not baseline or baseline.keys() != candidate.keys():
        raise ValueError("nonempty, matching task ids required")
    if any(type(v) is not bool for v in (*baseline.values(), *candidate.values())):
        raise TypeError("outcomes must be boolean")
    both = c_only = b_only = neither = 0
    for key in sorted(baseline):
        b, c = baseline[key], candidate[key]
        if b and c: both += 1
        elif c: c_only += 1
        elif b: b_only += 1
        else: neither += 1
    return both, c_only, b_only, neither


def mcnemar_exact(candidate_only, baseline_only):
    """Exact two-sided McNemar p value from discordant pairs; returns 1 for 0."""
    if any(type(x) is not int or x < 0 for x in (candidate_only, baseline_only)):
        raise ValueError("nonnegative integer counts required")
    n = candidate_only + baseline_only
    if not n:
        return 1.0
    k = min(candidate_only, baseline_only)
    # Sum only the shorter binomial tail to avoid floating-point overflow.
    tail = sum(comb(n, i) / 2**n for i in range(k + 1))
    return min(1.0, 2 * tail)


def wilson_interval(successes, trials, z=1.959963984540054):
    """Wilson score interval for one binomial proportion, NOT paired risk difference."""
    if type(successes) is not int or type(trials) is not int or trials <= 0 or not (0 <= successes <= trials):
        raise ValueError("invalid successes/trials")
    p = successes / trials
    d = 1 + z*z/trials
    center = (p + z*z/(2*trials))/d
    radius = z*sqrt((p*(1-p) + z*z/(4*trials))/trials)/d
    return max(0.0, center-radius), min(1.0, center+radius)


def holm_adjust(pvalues):
    """Holm step-down familywise adjustment, preserving input order."""
    if not pvalues or any(type(p) not in (int,float) or not 0 <= p <= 1 for p in pvalues):
        raise ValueError("pvalues must be finite numbers between 0 and 1")
    ranked = sorted(enumerate(pvalues), key=lambda x:(x[1],x[0]))
    adjusted = [0.0]*len(ranked)
    prev = 0.0
    for j,(index,p) in enumerate(ranked):
        prev = max(prev, min(1.0, (len(ranked)-j)*p))
        adjusted[index] = prev
    return adjusted
