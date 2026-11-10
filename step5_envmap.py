# step5_envmap.py ─ 환경값을 넣으면 '가장 유리한 검사 순서 지도(히트맵)'를 그린다
#   6단계: 6-1 (K, w에 따른 D·T 자리), 6-2 (현재 순서 L→Q→D→T가 1위인 칸 수),
#          6-3 (섞인 요청 전체의 통과율로 정한 규칙 순서 = 지도 1위?)
#   기록: fig4_envmap.png, envmap.csv
import csv
import random
import numpy as np
import matplotlib.pyplot as plt
from config import NAMES, ORDERS, arrow, rule_order, set_korean_font

COST = {"Q": 3, "L": 5, "D": 1, "T": 1}        # 1건 확인 시간(가상 설정)

def make_env(K=10, w=0.3, alphabet=36, length=4, parcels=10000, digits=4):
    """환경값 → 요청 종류별 '조건 통과 확률' (맞는 경우의 수 ÷ 풀의 크기)"""
    qr_pool = alphabet ** length                 # QR 코드로 만들 수 있는 모든 코드 수
    p_forge = min(1, parcels / qr_pool)          # 찍은 코드가 실제 운송장 하나와 맞을 확률
    p_pw = 1 / 10 ** digits                      # 비밀번호 풀에서 맞는 것은 1개
    p_driver = 1 / K                             # 기사 K명 중 담당은 1명
    return [  # (요청 비율, 조건별 통과 확률)
        (0.70, {"Q": 1,       "L": 1,    "D": 1,        "T": 1}),   # 정상 담당 기사
        (0.12, {"Q": 1,       "L": 1,    "D": p_driver, "T": 1}),   # 로그인한 다른 기사
        (0.15, {"Q": 1,       "L": p_pw, "D": p_driver, "T": w}),   # 운송장을 본 외부인
        (0.03, {"Q": p_forge, "L": p_pw, "D": p_driver, "T": w}),   # 코드를 찍어 보는 위조
    ]

def cost_one_type(order, p, cost=COST):
    """한 종류의 요청: 앞을 통과한 비율(alive)만큼만 다음 확인을 한다."""
    total, alive = 0, 1
    for k in order:
        total += alive * cost[k]
        alive *= p[k]
    return total

def expected_cost(order, env, cost=COST):
    """여러 종류가 섞인 요청: 종류별 시간 × 비율을 모두 더한다."""
    return sum(ratio * cost_one_type(order, p, cost) for ratio, p in env)

def simulate(order, env, n, seed=0, cost=COST):
    """같은 환경을 난수로 실험: 풀에서 하나 뽑아 '맞는 수' 안에 들면 통과."""
    random.seed(seed)
    ratios = [r for r, _ in env]
    total = 0
    for _ in range(n):
        _, p = random.choices(env, weights=ratios)[0]       # 요청 종류 뽑기
        for k in order:
            total += cost[k]
            if random.random() >= p[k]:                     # 통과 못 하면 멈춤
                break
    return total / n

def mixed_pass(env):
    """섞인 요청 전체에서 조건별 통과율 = Σ (요청 비율 × 그 종류의 통과 확률)"""
    return {k: sum(ratio * p[k] for ratio, p in env) for k in NAMES}

if __name__ == "__main__":
    set_korean_font()
    Ks = [1, 2, 3, 4, 5, 7, 10, 15, 20, 30, 50, 100]
    Ws = np.round(np.arange(0.05, 1.0001, 0.05), 2)

    # ① 한 환경의 요청 종류별 통과 확률표
    print("=== ① 요청 종류별 통과 확률표 (K = 10, w = 30%) ===")
    kinds_name = ["정상 담당 기사", "로그인한 다른 기사", "운송장을 본 외부인", "코드를 찍어 보는 위조"]
    for name, (ratio, p) in zip(kinds_name, make_env(K=10, w=0.3)):
        print(f"  {name:<14} {ratio:.0%}  " + "  ".join(f"{k} {p[k]:.6g}" for k in NAMES))

    best = [[None] * len(Ks) for _ in Ws]
    gain = np.zeros((len(Ws), len(Ks)))
    rows, rule_same, lqdt_best, lqdt_tie = [], 0, 0, 0
    for i, w in enumerate(Ws):
        for j, K in enumerate(Ks):
            env = make_env(K=K, w=w)
            res = {o: expected_cost(o, env) for o in ORDERS}      # 24가지 모두 계산
            best[i][j] = min(res, key=res.get)
            gain[i][j] = 100 * (1 - res[best[i][j]] / res["LQDT"])
            rule = rule_order(mixed_pass(env), COST)              # 6-3: 섞인 요청 전체의 통과율로 규칙 적용
            same = abs(res[rule] - res[best[i][j]]) < 1e-12
            rule_same += same
            lqdt_best += best[i][j] == "LQDT"
            lqdt_tie += abs(res["LQDT"] - res[best[i][j]]) < 1e-12
            b = best[i][j]
            rows.append([K, w, arrow(b), b.index("D") + 1, b.index("T") + 1,
                         round(gain[i][j], 3), arrow(rule), same])

    kinds = sorted({b for row in best for b in row})
    idx = np.array([[kinds.index(b) for b in row] for row in best])
    print("\n지도에 나타난 1위 순서:", kinds)
    for k in kinds:
        print(f"  {arrow(k)}: {sum(row.count(k) for row in best)}칸")

    fig, ax = plt.subplots(1, 2, figsize=(14, 5.2))
    im = ax[0].imshow(idx, origin="lower", aspect="auto",
                      cmap=plt.get_cmap("tab10", len(kinds)), vmin=-.5, vmax=len(kinds) - .5)
    bar = fig.colorbar(im, ax=ax[0], ticks=range(len(kinds)))
    bar.ax.set_yticklabels(["→".join(k) for k in kinds])
    im2 = ax[1].imshow(gain, origin="lower", aspect="auto", cmap="viridis")
    fig.colorbar(im2, ax=ax[1], label="절감률 (%)")
    for a in ax:
        a.set_xticks(range(len(Ks))); a.set_xticklabels(Ks)
        a.set_yticks(range(0, len(Ws), 2)); a.set_yticklabels([f"{x:.0%}" for x in Ws[::2]])
        a.set_xlabel("택배 기사 수 K"); a.set_ylabel("열람 가능 시간 비율 w")
    ax[0].set_title("환경별 1위 검사 순서"); ax[1].set_title("현재 순서 L→Q→D→T 대비 절감률")
    plt.tight_layout(); plt.savefig("fig4_envmap.png", dpi=150)

    # ② 한 칸을 골라 계산과 난수 실험이 맞는지 확인 (K=10, w=0.3)
    print("\n=== ② 계산과 난수 실험 비교 (K = 10, w = 30%, 10만 건) ===")
    env = make_env(K=10, w=0.3)
    for o in ["DTLQ", "LQDT"]:
        print(f"K=10, w=0.3, {o}: 계산 {expected_cost(o, env):.3f}, 실험 {simulate(o, env, 100000):.3f}")

    # 6-1: K가 커질 때 D의 자리, w가 커질 때 T의 자리
    print("\n=== 6-1 1위 순서에서 D·T의 평균 자리 (1 = 맨 앞, 4 = 맨 뒤) ===")
    print("  기사 수 K별 D의 평균 자리:", "  ".join(
        f"K={K}:{np.mean([r[3] for r in rows if r[0] == K]):.2f}" for K in Ks))
    print("  열람 비율 w별 T의 평균 자리:", "  ".join(
        f"{w:.0%}:{np.mean([r[4] for r in rows if r[1] == w]):.2f}" for w in Ws))

    # 6-2, 6-3
    n_cell = len(Ks) * len(Ws)
    print(f"\n=== 6-2 L→Q→D→T 가 1위인 칸: {lqdt_best}칸 / {n_cell}칸 "
          f"(1위와 시간이 같은 칸까지 세면 {lqdt_tie}칸) ===")
    print(f"=== 6-3 규칙 순서의 시간이 1위와 같은 칸: {rule_same}칸 / {n_cell}칸 ===")
    for r in rows:
        if not r[7]:
            print(f"  다른 칸: K={r[0]}, w={r[1]:.0%}  1위 {r[2]} / 규칙 {r[6]}")

    with open("envmap.csv", "w", newline="", encoding="utf-8-sig") as f:
        wr = csv.writer(f)
        wr.writerow(["K", "w", "1위 순서", "D 자리", "T 자리", "절감률(%)", "규칙 순서", "규칙=1위"])
        wr.writerows(rows)
    print("→ fig4_envmap.png, envmap.csv 저장 완료")
