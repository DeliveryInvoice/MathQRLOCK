"""step3_rule.py ─ 5단계: 가장 빠른 순서의 규칙은 무엇일까?

① 이웃한 두 문지기(Q와 D, Q와 L, L과 T)의 자리만 바꾸어 두 부분의 시간 비교
② 문지기별 '확인 시간 ÷ 거부 비율'
③ 규칙으로 정한 순서 vs 24가지 전체 계산의 1위 (가설 5-1)
④ 확인 시간을 모두 1로 바꾸면 1차 탐구의 규칙(많이 거부하는 문지기 먼저)과 같아지는가?
⑤ Q 통과 기준을 바꾼 다른 설정에서도 규칙이 맞는가?
"""
from config import NAMES, THRESH, COST, arrow, pass_rate, expected_time, rule_order, best_order


def pair_compare(X, Y, p, cost):
    """이웃한 X, Y 부분의 시간만 비교 (나머지 문지기의 시간은 변하지 않는다)."""
    x_first = cost[X] + p[X] * cost[Y]
    y_first = cost[Y] + p[Y] * cost[X]
    print(f"  {X} 먼저: {cost[X]} + {p[X]}×{cost[Y]} = {x_first:.3f}   |   "
          f"{Y} 먼저: {cost[Y]} + {p[Y]}×{cost[X]} = {y_first:.3f}   → "
          f"{X if x_first < y_first else Y if y_first < x_first else '같음'} 이(가) 앞")


def ratio_table(p, cost):
    print(f"  {'문지기':<6}{'확인 시간':>8}{'거부 비율':>10}{'시간 ÷ 거부 비율':>18}")
    for k in NAMES:
        reject = 1 - p[k]
        r = cost[k] / reject if reject > 0 else float("inf")
        print(f"  {k:<6}{cost[k]:>8}{reject:>10.2f}{r:>18.3f}")


def compare(p, cost, label):
    rule = rule_order(p, cost)
    best, res = best_order(p, cost)
    same = abs(res[rule] - res[best]) < 1e-12
    print(f"  [{label}] 규칙 순서 {arrow(rule)} ({res[rule]:.4f})  /  24가지 1위 {arrow(best)} ({res[best]:.4f})"
          f"  → {'같은 시간' if same else '다름'}")
    return same, res


if __name__ == "__main__":
    p = pass_rate()

    print("=== ① 이웃한 두 문지기 바꾸기 ===")
    for X, Y in [("Q", "D"), ("Q", "L"), ("L", "T")]:
        pair_compare(X, Y, p, COST)

    print("\n=== ② 문지기별 '확인 시간 ÷ 거부 비율' ===")
    ratio_table(p, COST)

    print("\n=== ③ 규칙 vs 24가지 전체 계산 — 가설 5-1 ===")
    _, res = compare(p, COST, "기본 설정")
    print("  24가지 중 1~5위:", " / ".join(f"{arrow(o)}({res[o]:.4f})" for o in sorted(res, key=res.get)[:5]))

    print("\n=== ④ 확인 시간을 모두 1로 바꾸면? ===")
    ones = {k: 1 for k in NAMES}
    ratio_table(p, ones)
    compare(p, ones, "시간 모두 1")
    reject_first = "".join(sorted(NAMES, key=lambda k: -(1 - p[k])))
    print(f"  1차 탐구 규칙(거부 비율이 큰 문지기 먼저): {arrow(reject_first)}"
          f"  ({expected_time(reject_first, p, ones):.4f})")

    print("\n=== ⑤ Q 통과 기준을 바꾼 설정에서도 규칙이 맞는가? ===")
    ok = 0
    for q in range(10, 100, 10):
        same, _ = compare(pass_rate(dict(THRESH, Q=q)), COST, f"Q 통과율 {q / 100:.1f}")
        ok += same
    print(f"  9가지 설정 중 규칙과 1위가 같은 시간인 설정: {ok}가지")
