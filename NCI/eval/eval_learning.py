"""NCI-006 independent learning evaluation. Calls NCI-004 run_episode/ExperienceStore UNMODIFIED.
Own task generator and reward environments; strong baselines incl. best-fixed chosen on a separate validation split."""
import random, json, sys, tempfile
from pathlib import Path
from skynet_native_learning import ExperienceStore, run_episode
from skynet_native_learning.benchmark import host

def task(tid, risk, fast_fails, safe_len, fast_cost, safe_fails=False):
    sfx = tid.replace(':', 'x'); facts = ['s' + sfx, 'g' + sfx] + ['m' + sfx + str(k) for k in range(safe_len - 1)]
    a = lambda n, x, y, c: dict(name=n, positive=[x], negative=[], add=[y], delete=[x], cost=c, fuel=0)
    acts = [a('fast' + sfx, facts[0], facts[1], fast_cost)]; nodes = [facts[0]] + facts[2:] + [facts[1]]; safe = []
    for k, (x, y) in enumerate(zip(nodes, nodes[1:])): safe.append('safe' + sfx + str(k)); acts.append(a('safe' + sfx + str(k), x, y, 1))
    m = dict(schema='nci003-v1', facts=facts, initial=[facts[0]], goal=[facts[1]], avoid=[], actions=acts, fuel=3, budget=32, max_expansions=500, max_steps=12, exclusive=[])
    return {'task_id': tid, 'features': {'risk': risk}, 'model': m, 'strategies': {'fast': [acts[0]['name']], 'safe': safe},
            'faults_by_strategy': {'fast': [{'attempt': 0, 'kind': 'FAIL'}] if fast_fails else [], 'safe': [{'attempt': 0, 'kind': 'FAIL'}] if safe_fails else []}}
ENVS = {  # name -> (fast_fails(risk, rng), safe_fails(risk, rng), safe_len, fast_cost)
    'A_replication_threshold50': (lambda r, g: r >= 50, lambda r, g: False, 3, 2),
    'B_boundary_shift_30': (lambda r, g: r >= 30, lambda r, g: False, 3, 2),
    'C_non_monotone_25_75': (lambda r, g: 25 <= r < 75, lambda r, g: False, 3, 2),
    'D_stochastic_p25_p75': (lambda r, g: g.random() < (0.75 if r >= 50 else 0.25), lambda r, g: False, 3, 2),
    'E_inverted_low_risk_fast_fails': (lambda r, g: r < 50, lambda r, g: False, 3, 2),
    'F_cost_shift_long_safe': (lambda r, g: r >= 50, lambda r, g: False, 7, 1)}
def split(env, name, n, seed):
    ff, sf, L, fc = ENVS[env]; g = random.Random(seed); out = []
    for i in range(n):
        r = g.randrange(0, 101); out.append(task('%s:%s:%d' % (env[0], name, i), r, ff(r, g), L, fc, sf(r, g)))
    return out
def ep(store, t, **kw): return run_episode(host(), store, t, **kw)
def m(rows): return {'n': len(rows), 'success_rate': round(sum(r['success'] for r in rows) / len(rows), 4), 'avg_reward': round(sum(r['reward'] for r in rows) / len(rows), 3)}
def evaluate_env(env, tmp, seed):
    tr, va, te = split(env, 'tr', 24, seed), split(env, 'va', 16, seed + 1), split(env, 'te', 24, seed + 2); out = {}
    s = ExperienceStore(Path(tmp) / (env + '-learned.json')); train = [ep(s, t, split='train') for t in tr]; params = s.parameters()
    learned = [ep(s, t) for t in te]
    rs = ExperienceStore(Path(tmp) / (env + '-learned.json')); restart = [ep(rs, dict(t, task_id=t['task_id'] + 'r')) for t in te]
    fixed = {k: [ep(ExperienceStore(Path(tmp) / (env + k + '.json')), t, fixed=k) for t in te] for k in ('fast', 'safe')}
    val = {k: m([ep(ExperienceStore(Path(tmp) / (env + 'val' + k + '.json')), t, fixed=k) for t in va])['avg_reward'] for k in ('fast', 'safe')}
    best = max(val, key=lambda k: (val[k], k == 'safe'))
    disabled = [ep(ExperienceStore(Path(tmp) / (env + '-disabled.json')), t, learn=False) for t in te]
    fb = ExperienceStore(Path(tmp) / (env + '-nofeedback.json'))
    for t in tr: ep(fb, t, split='train', feedback=False)
    nofb = [ep(fb, t) for t in te]
    oracle = [max(a['reward'], b['reward']) for a, b in zip(fixed['fast'], fixed['safe'])]
    curve = {}
    for n in (0, 4, 12):
        cs = ExperienceStore(Path(tmp) / ('%s-curve%d.json' % (env, n)))
        for t in tr[:n]: ep(cs, dict(t, task_id=t['task_id'] + 'c%d' % n), split='train')
        curve[n] = m([ep(cs, dict(t, task_id=t['task_id'] + 'c%d' % n)) for t in te])['avg_reward']
    out = {'train': m(train), 'learned': m(learned), 'restart': m(restart), 'restart_identical_choices': [r['strategy'] for r in learned] == [r['strategy'] for r in restart],
           'disabled_default': m(disabled), 'fixed_fast': m(fixed['fast']), 'fixed_safe': m(fixed['safe']), 'validation_avg_reward': val, 'best_fixed_by_validation': best,
           'best_fixed_test': m(fixed[best]), 'oracle_avg_reward': round(sum(oracle) / len(oracle), 3), 'feedback_removed': m(nofb), 'learning_curve_avg_reward': curve,
           'parameters_after_training': params}
    out['advantage_vs_best_fixed'] = round(out['learned']['avg_reward'] - out['best_fixed_test']['avg_reward'], 3)
    out['success_gain_vs_best_fixed'] = round(out['learned']['success_rate'] - out['best_fixed_test']['success_rate'], 4)
    out['generalization_gap_train_minus_test'] = round(out['train']['avg_reward'] - out['learned']['avg_reward'], 3)
    out['regret_vs_oracle'] = round(out['oracle_avg_reward'] - out['learned']['avg_reward'], 3)
    return out
if __name__ == '__main__':
    with tempfile.TemporaryDirectory() as tmp:
        res = {env: evaluate_env(env, tmp, 6060 + 10 * i) for i, env in enumerate(ENVS)}
    res['_unseen_feature_probe'] = {}
    try:
        from skynet_native_learning import context; context({'risk': 10, 'weather': 1}); res['_unseen_feature_probe'] = 'ACCEPTED'
    except Exception as e: res['_unseen_feature_probe'] = 'REJECTED:' + str(e)
    json.dump(res, open(sys.argv[1], 'w'), indent=1)
    for env, r in res.items():
        if env.startswith('_'): print(env, r); continue
        print(env, '| learned', r['learned'], '| best_fixed', r['best_fixed_by_validation'], r['best_fixed_test'], '| adv', r['advantage_vs_best_fixed'], '| oracle', r['oracle_avg_reward'],
              '| disabled', r['disabled_default']['avg_reward'], '| nofb', r['feedback_removed']['avg_reward'], '| curve', r['learning_curve_avg_reward'], '| restart', r['restart_identical_choices'], '| gap', r['generalization_gap_train_minus_test'])
