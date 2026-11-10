"""step4_apply.py ─ 7단계: 실제 QRLOCK에서는? (로그인 먼저, 로그인 유지)

① L로 시작하는 순서를 수형도로 세기 (3×2×1)
② 6가지 순서의 평균 확인 시간: 계산과 실험 (단순 모형, 2층 모형 K=10·w=30%)
   → 1위가 규칙으로 정한 순서와 같은가? (가설 7-1)
③ 로그인 유지: L의 확인 시간을 5 → 0 으로 바꾸어 다시 구하기 (가설 7-2)
④ 현재 QRLOCK 순서(L→Q→D→T)와 비교
기록: apply_results.csv
"""
import csv

import numpy as np

from config import NAMES, ORDERS, COST, SEEDS, arrow, pass_rate, expected_time, make_requests, measure, rule_order
from step5_envmap import make_env, expected_cost, simulate

L_ORDERS = [o for o in ORDERS if o[0] == "L"]
REST = [k for k in NAMES if k != "L"]
COST_KEEP = dict(COST, L=0)                     # 로그인 유지: L 확인 시간 0


def tree():
    print("=== ① L로 시작하는 순서 (수형도) ===")
    for a in REST:
        others = [k for k in REST if k != a]
        for b in others:
            c = [k for k in others if k != b][0]
            print(f"  L ─ {a} ─ {b} ─ {c}")
    print(f"  프로그램으로 센 개수: {len(L_ORDERS)}가지  (수형도: 3×2×1 = {3 * 2 * 1})\n")


def simple_model(cost, n=10000):
    """단순 모형: 계산값과 실험값(요청 10,000건, seed 0~4 평균)"""
    p = pass_rate()
    reqs = [make_requests(n, s) for s in SEEDS]
    out = {o: (expected_time(o, p, cost), np.mean([measure(o, r, cost) for r in reqs])) for o in L_ORDERS}
    rule = "L" + rule_order(p, cost, REST)
    return out, rule


def env_model(cost, K=10, w=0.3, n=100000):
    """2층 모형: 계산값과 실험값(10만 건)"""
    env = make_env(K=K, w=w)
    out = {o: (expected_cost(o, env, cost), simulate(o, env, n, cost=cost)) for o in L_ORDERS}
    # 뒤의 세 문지기는 L을 통과한 요청만 만나므로, L을 통과한 요청 안에서의 통과율로 규칙을 적용한다.
    pass_l = sum(r * p["L"] for r, p in env)
    p_after = {k: sum(r * p["L"] * p[k] for r, p in env) / pass_l for k in REST}
    rule = "L" + rule_order(p_after, cost, REST)
    return out, rule


def report(name, out, rule):
    ranked = sorted(out, key=lambda o: out[o][0])
    print(f"  [{name}]")
    print(f"  {'순위':>4}  {'순서':<10}{'계산':>10}{'실험':>10}")
    for i, o in enumerate(ranked, 1):
        print(f"  {i:>4}  {arrow(o):<10}{out[o][0]:>10.4f}{out[o][1]:>10.4f}")
    same = abs(out[rule][0] - out[ranked[0]][0]) < 1e-12
    print(f"  규칙으로 정한 순서: {arrow(rule)}  → 1위와 {'같은 시간' if same else '다름'}\n")
    return ranked[0]


if __name__ == "__main__":
    tree()
    rows = []
    for model, fn in [("단순 모형", simple_model), ("2층 모형 K=10, w=30%", env_model)]:
        print(f"=== ②③ {model} ===")
        before, rule_b = fn(COST)
        after, rule_a = fn(COST_KEEP)
        best_b = report("로그인 매번 확인 (L = 5)", before, rule_b)
        best_a = report("로그인 유지 (L = 0)", after, rule_a)

        print("  로그인 유지 전후 비교")
        print(f"  {'순서':<10}{'전(계산)':>10}{'후(계산)':>10}{'줄어든 양':>10}{'전(실험)':>10}{'후(실험)':>10}")
        for o in L_ORDERS:
            (cb, eb), (ca, ea) = before[o], after[o]
            print(f"  {arrow(o):<10}{cb:>10.4f}{ca:>10.4f}{cb - ca:>10.4f}{eb:>10.4f}{ea:>10.4f}")
            rows.append([model, arrow(o), cb, eb, ca, ea])

        cur = before["LQDT"][0]
        print(f"\n  ④ 현재 순서 L→Q→D→T (로그인 매번): {cur:.4f}")
        print(f"     L 고정 1위 {arrow(best_b)} (로그인 매번): {before[best_b][0]:.4f}"
              f"  → {100 * (1 - before[best_b][0] / cur):.2f}% 절감")
        print(f"     L 고정 1위 {arrow(best_a)} (로그인 유지): {after[best_a][0]:.4f}"
              f"  → {100 * (1 - after[best_a][0] / cur):.2f}% 절감\n")

    with open("apply_results.csv", "w", newline="", encoding="utf-8-sig") as f:
        w = csv.writer(f)
        w.writerow(["모형", "순서", "로그인매번_계산", "로그인매번_실험", "로그인유지_계산", "로그인유지_실험"])
        w.writerows(rows)
    print("→ apply_results.csv 저장 완료")
