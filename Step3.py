"""step2_rare.py ─ 2단계(2-2): 풀 20,000개 중 1개를 맞힐 확률을 실험으로 확인하기

1만 번, 10만 번, 100만 번, 200만 번씩 (seed 3번) 찍어 보고 맞힌 횟수와 실험 확률을 기록한다.
판단 기준(가설 2-2): 200만 번 실험의 실험 확률이 seed 3번 모두 0.00004~0.00006 안,
                    1만 번 실험은 그렇지 않음.
기록: rare_results.csv
"""
import csv

import numpy as np

POOL = 20000            # 만들 수 있는 비밀번호 수 (풀의 크기)
ANSWER = 1              # 맞는 비밀번호 (풀 안의 아무 수 하나)
TRIALS = [10_000, 100_000, 1_000_000, 2_000_000]
SEEDS = [0, 1, 2]
LOW, HIGH = 0.00004, 0.00006

if __name__ == "__main__":
    true_p = 1 / POOL
    print(f"세어서 구한 확률: 1 ÷ {POOL:,} = {true_p:.6f}\n")
    print(f"{'실험 횟수':>12}{'seed':>6}{'맞힌 횟수':>10}{'실험 확률':>12}   0.00004~0.00006 안?")

    rows = []
    for n in TRIALS:
        for s in SEEDS:
            rng = np.random.default_rng(s)
            guesses = rng.integers(1, POOL + 1, size=n)     # 1~20,000 중 하나씩 찍기
            hits = int((guesses == ANSWER).sum())
            p = hits / n
            inside = LOW <= p <= HIGH
            rows.append([n, s, hits, p, inside])
            print(f"{n:>12,}{s:>6}{hits:>10}{p:>12.6f}   {'예' if inside else '아니오'}")
        print()

    print("실험 횟수별 정리")
    for n in TRIALS:
        sub = [r for r in rows if r[0] == n]
        print(f"  {n:>10,}번: 맞힘 {[r[2] for r in sub]}, 범위 안 {sum(r[4] for r in sub)}/{len(sub)}")

    with open("rare_results.csv", "w", newline="", encoding="utf-8-sig") as f:
        w = csv.writer(f)
        w.writerow(["실험 횟수", "seed", "맞힌 횟수", "실험 확률", "0.00004~0.00006 안"])
        w.writerows(rows)
    print("→ rare_results.csv 저장 완료")
