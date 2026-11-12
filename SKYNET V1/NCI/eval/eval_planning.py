"""NCI-006 independent planning evaluation. Task generator, simulator, optimal reference (Dijkstra over
(state,fuel,steps)) and baselines are written independently of NCI-003 code and benchmark. The planner
(skynet_native_planning.core.search / integration.execute_goal) is only the system under test."""
import random, heapq, json, sys, itertools, copy
from skynet_native_planning.core import parse, search, PlanningError
from skynet_native_planning.integration import execute_goal, verify_execution

SEED = 60061
def act(name, pos, add, dele, cost=1, fuel=0, neg=()):
    return dict(name=name, positive=sorted(set(pos)), negative=sorted(set(neg)), add=sorted(set(add)), delete=sorted(set(dele)), cost=cost, fuel=fuel)
def model(facts, init, goal, actions, avoid=(), fuel=0, budget=64, steps=12, excl=(), maxexp=5000):
    return {'schema': 'nci003-v1', 'facts': sorted(set(facts)), 'initial': sorted(set(init)), 'goal': sorted(set(goal)), 'avoid': sorted(set(avoid)),
            'actions': actions, 'fuel': fuel, 'budget': budget, 'max_expansions': maxexp, 'max_steps': steps, 'exclusive': [sorted(x) for x in excl]}

# ---------------- independent semantics -----------------
def ok_excl(m, s): return all(len(s & set(x)) <= 1 for x in m['exclusive'])
def app(m, a, s, f): return set(a['positive']) <= s and not (set(a['negative']) & s) and a['fuel'] <= f and ok_excl(m, (s - set(a['delete'])) | set(a['add']))
def nxt(a, s, f): return frozenset((s - set(a['delete'])) | set(a['add'])), f - a['fuel']
def goal_ok(m, s): return set(m['goal']) <= s and not (set(m['avoid']) & s)
def simulate(m, plan):
    s, f, c, by = frozenset(m['initial']), m['fuel'], 0, {a['name']: a for a in m['actions']}
    for n in plan:
        a = by.get(n)
        if a is None or not app(m, a, s, f): return False, 'INAPPLICABLE', c
        c += a['cost']
        if c > m['budget']: return False, 'BUDGET', c
        s, f = nxt(a, s, f)
    if len(plan) > m['max_steps']: return False, 'STEPS', c
    return goal_ok(m, s), ('OK' if goal_ok(m, s) else 'GOAL'), c
def reference(m):
    """Exact optimal cost by plain Dijkstra over labels (state, fuel, steps) under step/budget limits."""
    s0 = frozenset(m['initial']); q = [(0, 0, sorted(s0), s0, m['fuel'])]; best = {(s0, m['fuel'], 0): 0}; exp = 0; deeper = False
    while q:
        c, k, _, s, f = heapq.heappop(q)
        if best.get((s, f, k)) != c: continue
        if goal_ok(m, s): return {'class': 'REACHABLE', 'cost': c, 'expansions': exp}
        exp += 1
        for a in m['actions']:
            if not app(m, a, s, f) or c + a['cost'] > m['budget']: continue
            if k >= m['max_steps']: deeper = True; continue
            ns, nf = nxt(a, s, f); key = (ns, nf, k + 1)
            if best.get(key, 10**9) > c + a['cost']: best[key] = c + a['cost']; heapq.heappush(q, (c + a['cost'], k + 1, sorted(ns), ns, nf))
    if deeper:  # STEP_LIMIT only if the goal is reachable at all when the step cap is lifted (closure, budget-free)
        seen = {(s0, m['fuel'])}; st = [(s0, m['fuel'])]
        while st:
            s, f = st.pop()
            if goal_ok(m, s): return {'class': 'STEP_LIMIT', 'cost': None, 'expansions': exp}
            for a in m['actions']:
                if app(m, a, s, f):
                    n = nxt(a, s, f)
                    if n not in seen: seen.add(n); st.append(n)
    return {'class': 'UNREACHABLE', 'cost': None, 'expansions': exp}
def baseline(m, kind):
    s, f, c, plan, visited = frozenset(m['initial']), m['fuel'], 0, [], {frozenset(m['initial'])}
    while not goal_ok(m, s) and len(plan) < m['max_steps']:
        cands = [a for a in m['actions'] if app(m, a, s, f) and c + a['cost'] <= m['budget'] and nxt(a, s, f)[0] not in visited]
        if not cands: break
        if kind == 'greedy':
            score = lambda a: (-len(set(m['goal']) & nxt(a, s, f)[0]) + len(set(m['avoid']) & nxt(a, s, f)[0]), a['cost'], a['name'])
            a = min(cands, key=score)
        else: a = cands[0]  # fixed: first applicable action in supplied order
        plan.append(a['name']); c += a['cost']; s, f = nxt(a, s, f); visited.add(s)
    return plan

# ---------------- independent task families -----------------
def blocks(rng, k):
    B = 'ABC'; F = ['he'] + ['ot' + x for x in B] + ['cl' + x for x in B] + ['ho' + x for x in B] + ['on' + x + y for x in B for y in B if x != y]; A = []
    for x in B:
        A.append(act('pick' + x, ['cl' + x, 'ot' + x, 'he'], ['ho' + x], ['cl' + x, 'ot' + x, 'he']))
        A.append(act('put' + x, ['ho' + x], ['ot' + x, 'cl' + x, 'he'], ['ho' + x]))
        for y in B:
            if x != y:
                A.append(act('st' + x + y, ['ho' + x, 'cl' + y], ['on' + x + y, 'cl' + x, 'he'], ['ho' + x, 'cl' + y]))
                A.append(act('un' + x + y, ['on' + x + y, 'cl' + x, 'he'], ['ho' + x, 'cl' + y], ['on' + x + y, 'cl' + x, 'he']))
    def config():
        bl = list(B); rng.shuffle(bl); cut = sorted(rng.sample(range(1, 3), rng.randint(0, 2))); stacks = [bl[i:j] for i, j in zip([0] + cut, cut + [3])]
        st = {'he'}
        for stk in stacks:
            st.add('ot' + stk[0]); st.add('cl' + stk[-1]); st |= {'on' + a + b for b, a in zip(stk, stk[1:])}
        return st, stacks
    if k == 0: init, goal = {'he', 'otA', 'otB', 'onCA', 'clC', 'clB'}, {'onAB', 'onBC'}  # Sussman anomaly
    else:
        init, _ = config(); g, stacks = config(); goal = {x for x in g if x.startswith('on')} or {'otA', 'otB', 'otC'}
    rng.shuffle(A)
    return model(F, init, goal, A, excl=[['he', 'hoA', 'hoB', 'hoC']])
def grid(rng, k):
    n = 3; P = lambda r, c: 'p%d%d' % (r, c); cells = [(r, c) for r in range(n) for c in range(n)]
    key = rng.choice(cells[1:]); door = {(rng.randrange(n), 1)}; A = []
    for (r, c) in cells:
        for dr, dc in ((0, 1), (1, 0), (0, -1), (-1, 0)):
            r2, c2 = r + dr, c + dc
            if 0 <= r2 < n and 0 <= c2 < n:
                need_key = ((r2, c2) in door or (r, c) in door) and k % 2 == 1
                A.append(act('m%d%d%d%d' % (r, c, r2, c2), [P(r, c)] + (['key'] if need_key else []), [P(r2, c2)], [P(r, c)], cost=1 + rng.randint(0, 2)))
    A.append(act('grab', [P(*key), 'kh'], ['key'], ['kh'])); rng.shuffle(A)
    tgt = rng.choice(cells[2:]); goal = [P(*tgt)] + (['key'] if k % 3 == 0 else [])
    return model([P(*x) for x in cells] + ['key', 'kh'], [P(0, 0), 'kh'], goal, A[:32], excl=[[P(*x) for x in cells]], budget=40)
def resources(rng, k):
    L = 4; F = ['n%d' % i for i in range(L + 1)]; A = []
    for i in range(L):
        A.append(act('fast%d' % i, [F[i]], [F[i + 1]], [F[i]], cost=1, fuel=2))
        A.append(act('slow%d' % i, [F[i]], [F[i + 1]], [F[i]], cost=3, fuel=0))
    A.append(act('jump', [F[0]], [F[L]], [F[0]], cost=rng.randint(6, 14), fuel=0)); rng.shuffle(A)
    fuel = rng.choice([0, 2, 4, 8]); budget = rng.choice([6, 8, 10, 20]) if k < 6 else 3
    return model(F, [F[0]], [F[L]], A, fuel=fuel, budget=budget)
def cyclic(rng, k):
    R = 5; F = ['r%d' % i for i in range(R)] + ['out']; A = []
    for i in range(R):
        A.append(act('cw%d' % i, ['r%d' % i], ['r%d' % ((i + 1) % R)], ['r%d' % i], cost=rng.randint(1, 3)))
        A.append(act('ccw%d' % i, ['r%d' % i], ['r%d' % ((i - 1) % R)], ['r%d' % i], cost=rng.randint(1, 3)))
    if k % 2 == 0: e = rng.randrange(1, R); A.append(act('exit', ['r%d' % e], ['out'], ['r%d' % e]))
    rng.shuffle(A); return model(F, ['r0'], ['out'], A, excl=[F])
def contradictory(rng, k):
    F = ['a', 'b', 'c', 'd']; A = [act('ab', ['a'], ['b'], ['a']), act('bc', ['b'], ['c'], ['b'])]
    if k % 3 == 0: return model(F, ['a'], ['c'], A, avoid=['c'])
    if k % 3 == 1: return model(F, ['a'], ['b', 'c'], A, excl=[['b', 'c']])
    bad = dict(act('x', ['a'], ['d'], []), negative=['a']); return model(F, ['a'], ['d'], A + [bad])
def unreachable(rng, k):
    if k % 2 == 0:
        F = ['s', 'm', 'g', 'z']; A = [act('sm', ['s'], ['m'], ['s']), act('ms', ['m'], ['s'], ['m']), act('mz', ['m', 'g'], ['z'], [])]
        return model(F, ['s'], ['g'], A)
    L = 14; F = ['c%d' % i for i in range(L + 1)]; A = [act('c%d' % i, ['c%d' % i], ['c%d' % (i + 1)], ['c%d' % i]) for i in range(L)]
    return model(F, ['c0'], ['c%d' % L], A, budget=100)  # reachable only beyond 12 steps
def alternatives(rng, k):
    F = ['s', 'g', 'x', 'y', 'w', 'lock', 'alarm']; A = [act('direct', ['s'], ['g'], ['s'], cost=rng.randint(4, 9)),
        act('sx', ['s'], ['x'], ['s'], cost=1), act('xy', ['x'], ['y'], ['x'], cost=1), act('yg', ['y'], ['g'], ['y'], cost=rng.randint(1, 4)),
        act('sw', ['s'], ['w', 'alarm'], ['s'], cost=1), act('wg', ['w'], ['g'], ['w'], cost=1), act('quiet', ['alarm'], [], ['alarm'], cost=rng.randint(1, 5)),
        act('guarded', ['x'], ['g'], ['x'], cost=1, neg=['lock'])]
    init = ['s'] + (['lock'] if k % 2 else []); rng.shuffle(A)
    return model(F, init, ['g'], A, avoid=['alarm'])
FAMILIES = {'blocks': blocks, 'grid_keys': grid, 'resources': resources, 'cyclic': cyclic, 'contradictory': contradictory,
            'unreachable_or_depth': unreachable, 'alternatives_negative_avoid': alternatives}

def run():
    rng = random.Random(SEED); rows = []
    for fam, gen in FAMILIES.items():
        for k in range(8):
            m = gen(rng, k); row = {'family': fam, 'k': k}
            try: d = parse(m)
            except PlanningError as e:
                row.update(planner='INVALID', reason=str(e), reference='INVALID_BY_CONSTRUCTION' if fam == 'contradictory' else 'UNEXPECTED_INVALID'); rows.append(row); continue
            ref = reference(m); r = search(d).json(); row.update(reference=ref['class'], ref_cost=ref['cost'], planner=r['status'], reason=r['reason'], cost=r['cost'],
                                                           expansions=r['expansions'], generated=r['generated'], ref_expansions=ref['expansions'], plan_len=len(r['plan']))
            if r['status'] == 'FOUND':
                valid, why, c = simulate(m, r['plan']); row.update(valid=valid, sim=why, sim_cost=c, optimal=(c == ref['cost']), gap=(None if ref['cost'] is None else c - ref['cost']))
            row['class_agrees'] = {'FOUND': 'REACHABLE', 'UNREACHABLE': 'UNREACHABLE', 'LIMIT': 'STEP_LIMIT'}.get(r['status']) == ref['class'] or (r['status'] == 'LIMIT' and r['reason'] != 'STEP_LIMIT' and ref['class'] == 'REACHABLE' and False)
            for kind in ('fixed', 'greedy'):
                p = baseline(m, kind); v, why, c = simulate(m, p); row[kind] = {'success': v, 'cost': c if v else None, 'gap': (c - ref['cost']) if v and ref['cost'] is not None else None, 'why': why}
            rows.append(row)
    return rows
def summarize(rows):
    S = {}
    for fam in FAMILIES:
        rs = [r for r in rows if r['family'] == fam]; reach = [r for r in rs if r.get('reference') == 'REACHABLE']
        S[fam] = {'cases': len(rs), 'reachable_by_reference': len(reach),
                  'planner_success': sum(r.get('valid', False) for r in reach), 'planner_optimal': sum(r.get('optimal', False) for r in reach),
                  'invalid_plans': sum(1 for r in rs if r.get('planner') == 'FOUND' and not r.get('valid')),
                  'classification_agreement': sum(1 for r in rs if r.get('class_agrees') or (r.get('planner') == 'INVALID' and r.get('reference') == 'INVALID_BY_CONSTRUCTION')),
                  'fixed_success': sum(r['fixed']['success'] for r in reach), 'greedy_success': sum(r['greedy']['success'] for r in reach),
                  'fixed_mean_gap': (lambda g: sum(g) / len(g) if g else None)([r['fixed']['gap'] for r in reach if r['fixed']['gap'] is not None]),
                  'greedy_mean_gap': (lambda g: sum(g) / len(g) if g else None)([r['greedy']['gap'] for r in reach if r['greedy']['gap'] is not None]),
                  'mean_expansions': (lambda g: sum(g) / len(g) if g else None)([r['expansions'] for r in rs if 'expansions' in r]),
                  'max_expansions': max([r['expansions'] for r in rs if 'expansions' in r], default=None)}
    return S
if __name__ == '__main__':
    rows = run(); s = summarize(rows); json.dump({'seed': SEED, 'rows': rows, 'summary': s}, open(sys.argv[1], 'w'), indent=1, default=str)
    tot = {k: sum(v[k] for v in s.values()) for k in ('cases', 'reachable_by_reference', 'planner_success', 'planner_optimal', 'invalid_plans', 'classification_agreement', 'fixed_success', 'greedy_success')}
    print(json.dumps(s, indent=0)); print('TOTAL', tot)
