"""step3_fit.py ─ 4단계(피팅)와 5단계 ④(두 직선의 교점)

먼저 step2_test.py 를 실행해 results.csv, threshold_results.csv 를 만들어 두어야 한다.
① Q→L→D→T 표 계산 (Ⅱ-5 방식)    ② 계산식 함수와 비교
③ 계산값-실험값 그래프 (fig1_fit.png), 평균 오차 (가설 4-1)
④ 요청 수별 오차, 로그 눈금 기울기 (fig2_error.png, 가설 4-2)
⑤ 실험 1위와 계산 1위 비교 (가설 3-2 판정이 운인지 규칙인지)
5단계 ④ Q 통과율에 따른 두 순서의 직선과 교점 (fig3_cross.png, 가설 5-2)
"""
import csv

import numpy as np
import matplotlib.pyplot as plt

from config import NAMES, ORDERS, THRESH, COST, SIZES, SEEDS, arrow, pass_rate, expected_time, set_korean_font


def load(path):
    with open(path, encoding="utf-8-sig") as f:
        return list(csv.DictReader(f))


def hand_table(order="QLDT", n=10000):
    print(f"=== ① {arrow(order)} 표 계산 (요청 {n:,}건) ===")
    p = pass_rate()
    print(f"{'문지기':<6}{'확인받는 요청':>12}{'1건 시간':>8}{'걸린 시간 합':>12}{'다음으로 가는 요청':>18}")
    alive, total = n, 0
    for k in order:
        spent, nxt = alive * COST[k], alive * p[k]
        print(f"{k:<6}{alive:>12,.0f}{COST[k]:>8}{spent:>12,.0f}{nxt:>14,.0f} (×{p[k]})")
        total += spent
        alive = nxt
    print(f"합계 {total:,.0f}  → 1건당 {total / n:.4f}")
    print(f"\n=== ② 계산식 함수 expected_time() 의 값: {expected_time(order, p):.4f} ===")
    print("→ 공책의 손 계산, 위 표, 함수 값이 모두 같은지 확인하세요.\n")


def fit_check(rows):
    print("=== ③ 계산값과 실험값 비교 (요청 10,000건) — 가설 4-1 ===")
    sub = [r for r in rows if int(r["요청수"]) == 10000]
    for s in SEEDS:
        errs = [abs(float(r["실험값"]) - float(r["계산값"])) for r in sub if int(r["seed"]) == s]
        print(f"  seed {s}: 24가지 순서의 평균 오차 {np.mean(errs):.4f}")
    all_err = np.mean([abs(float(r["실험값"]) - float(r["계산값"])) for r in sub])
    print(f"  전체 평균 오차: {all_err:.4f}  (판단 기준: 0.05 이하)\n")

    x = [float(r["계산값"]) for r in sub]
    y = [float(r["실험값"]) for r in sub]
    plt.figure(figsize=(5.5, 5.5))
    plt.scatter(x, y, s=18, alpha=0.6, label="24가지 순서 × seed 5번")
    lo, hi = min(x + y) - 0.1, max(x + y) + 0.1
    plt.plot([lo, hi], [lo, hi], "k--", lw=1, label="y = x")
    plt.xlabel("계산값 (평균 확인 시간)")
    plt.ylabel("실험값 (평균 확인 시간)")
    plt.title("계산값과 실험값 (요청 10,000건)")
    plt.legend()
    plt.tight_layout()
    plt.savefig("fig1_fit.png", dpi=150)
    plt.close()

    print("=== ④ 요청 수별 오차 — 가설 4-2 ===")
    ns, es = [], []
    for n in SIZES:
        errs = [abs(float(r["실험값"]) - float(r["계산값"])) for r in rows if int(r["요청수"]) == n]
        ns.append(n)
        es.append(np.mean(errs))
        print(f"  요청 {n:>7,}건: 평균 오차 {es[-1]:.5f}")
    slope, inter = np.polyfit(np.log10(ns), np.log10(es), 1)
    print(f"  로그 눈금 직선의 기울기: {slope:.3f}  (판단 기준: −0.6 ~ −0.4)")
    print(f"  → 요청 수 100배일 때 오차는 약 {100 ** slope:.3f}배\n")

    plt.figure(figsize=(6, 4.5))
    plt.loglog(ns, es, "o", label="실험 오차")
    xs = np.logspace(np.log10(ns[0]), np.log10(ns[-1]), 50)
    plt.loglog(xs, 10 ** inter * xs ** slope, "-", label=f"맞춘 직선 (기울기 {slope:.2f})")
    plt.xlabel("요청 수")
    plt.ylabel("평균 오차")
    plt.title("요청 수에 따른 오차")
    plt.legend()
    plt.tight_layout()
    plt.savefig("fig2_error.png", dpi=150)
    plt.close()

    print("=== ⑤ 실험 1위와 계산 1위 비교 (요청 10,000건) ===")
    p = pass_rate()
    calc_res = {o: expected_time(o, p) for o in ORDERS}
    calc_rank = sorted(ORDERS, key=calc_res.get)
    print("  계산 1~3위: " + " / ".join(f"{arrow(o)}({calc_res[o]:.4f})" for o in calc_rank[:3]))
    print(f"  계산으로 본 Q→L→D→T 의 순위: {calc_rank.index('QLDT') + 1}위")
    for s in SEEDS:
        top = next(r["순서"] for r in sub if int(r["seed"]) == s and int(r["순위"]) == 1)
        print(f"  seed {s} 실험 1위: {arrow(top)}  {'(계산 1위와 같음)' if top == calc_rank[0] else '(계산 1위와 다름)'}")
    print()


def cross_point(rows):
    print("=== 5단계 ④ 두 직선의 교점 — 가설 5-2 ===")
    qs = sorted({int(r["Q기준"]) for r in rows})
    x = np.array(qs) / 100
    y1 = np.array([np.mean([float(r["QDLT_실험"]) for r in rows if int(r["Q기준"]) == q]) for q in qs])
    y2 = np.array([np.mean([float(r["DQLT_실험"]) for r in rows if int(r["Q기준"]) == q]) for q in qs])
    a1, b1 = np.polyfit(x, y1, 1)
    a2, b2 = np.polyfit(x, y2, 1)
    cross = (b2 - b1) / (a1 - a2)

    # 계산으로 예측한 지점: Q와 D의 '확인 시간 ÷ 거부 비율'이 같아지는 Q 통과율
    p_d = THRESH["D"] / 100
    pred = 1 - COST["Q"] * (1 - p_d) / COST["D"]

    print(f"  Q→D→L→T 직선: y = {a1:.4f} x + {b1:.4f}")
    print(f"  D→Q→L→T 직선: y = {a2:.4f} x + {b2:.4f}")
    print(f"  두 직선의 교점: Q 통과율 = {cross:.4f}")
    print(f"  예측한 지점 (3 ÷ (1 − q) = 1 ÷ (1 − {p_d}) 인 q): {pred:.4f}")
    print(f"  차이: {abs(cross - pred):.4f}  (판단 기준: ±0.05 안)")

    plt.figure(figsize=(6.5, 4.5))
    plt.plot(x, y1, "o", color="C0", label="Q→D→L→T 실험")
    plt.plot(x, y2, "s", color="C1", label="D→Q→L→T 실험")
    xs = np.linspace(0, 1, 50)
    plt.plot(xs, a1 * xs + b1, "-", color="C0")
    plt.plot(xs, a2 * xs + b2, "-", color="C1")
    plt.axvline(cross, color="gray", ls="--", lw=1)
    plt.text(cross, plt.ylim()[0], f" 교점 {cross:.3f}", va="bottom")
    plt.xlabel("Q 통과율")
    plt.ylabel("평균 확인 시간")
    plt.title("Q 통과율에 따른 두 순서의 평균 확인 시간")
    plt.legend()
    plt.tight_layout()
    plt.savefig("fig3_cross.png", dpi=150)
    plt.close()


if __name__ == "__main__":
    set_korean_font()
    hand_table()
    fit_check(load("results.csv"))
    cross_point(load("threshold_results.csv"))
    print("→ fig1_fit.png, fig2_error.png, fig3_cross.png 저장 완료")
