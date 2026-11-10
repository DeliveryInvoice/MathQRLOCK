"""step1_pool.py ─ 2단계(2-1): 풀에서 만족하는 경우를 직접 세어 확률 구하기

① 모눈종이 10×10칸 넓이 모델 (가로 10칸 중 6칸, 세로 10칸 중 7칸)
② 1~20 풀 네 개에서 160,000가지 조합을 하나씩 확인해 네 조건을 모두 만족하는 개수 세기
   → 12×14×16×19 로 곱한 개수와 같은지 비교 (가설 2-1)
기록: pool_compare.csv
"""
import csv
from itertools import product

from config import NAMES

# ── ① 모눈종이 넓이 모델 ──────────────────────────────────
W, H = 10, 10
OK_X, OK_Y = 6, 7       # 가로 조건: 1~6이면 만족, 세로 조건: 1~7이면 만족

# ── ② 1~20 풀 ─────────────────────────────────────────────
POOL = 20
LIMIT = {"Q": 12, "L": 14, "D": 16, "T": 19}   # 각 조건: 1~20 중 이 수 이하이면 만족

if __name__ == "__main__":
    print("=== ① 모눈종이 10×10칸 ===")
    count = 0
    for y in range(H, 0, -1):                 # 위쪽 줄부터 그린다
        line = ""
        for x in range(1, W + 1):
            both = x <= OK_X and y <= OK_Y
            count += both
            line += "■" if both else "□"
        print(line)
    print(f"두 조건을 함께 만족하는 칸: {count}칸 / {W * H}칸  (곱: {OK_X}×{OK_Y} = {OK_X * OK_Y})")
    print("→ 모눈종이에 색칠한 칸 수와 비교하세요.\n")

    print("=== ② 1~20 풀에서 160,000가지 하나씩 세기 ===")
    single = {k: 0 for k in NAMES}
    total, all_ok = 0, 0
    for combo in product(range(1, POOL + 1), repeat=4):   # (Q, L, D, T) 값
        total += 1
        oks = [combo[i] <= LIMIT[k] for i, k in enumerate(NAMES)]
        for i, k in enumerate(NAMES):
            single[k] += oks[i]
        all_ok += all(oks)

    by_product = 1
    for k in NAMES:
        by_product *= LIMIT[k]

    print(f"전체 조합 수: {total:,}가지 (= {POOL}^4)")
    for k in NAMES:
        # 한 조건만 보면, 나머지 세 자리는 아무 값이나 되므로 20^3배가 된다.
        print(f"  {k}를 만족하는 값: {LIMIT[k]}개 / {POOL}  → 확률 {LIMIT[k]}/{POOL} = {LIMIT[k] / POOL}"
              f"   (160,000가지 중 {single[k]:,}가지)")
    print(f"네 조건을 모두 만족: 직접 센 개수 {all_ok:,}  /  곱한 개수 "
          f"{'×'.join(str(LIMIT[k]) for k in NAMES)} = {by_product:,}")
    print(f"두 값이 같은가? {'같다' if all_ok == by_product else '다르다'}")
    print(f"네 조건을 모두 만족할 확률: {all_ok:,} ÷ {total:,} = {all_ok / total:.6f}")

    with open("pool_compare.csv", "w", newline="", encoding="utf-8-sig") as f:
        w = csv.writer(f)
        w.writerow(["항목", "직접 센 개수", "곱한 개수", "같은가"])
        w.writerow(["모눈종이 10×10", count, OK_X * OK_Y, count == OK_X * OK_Y])
        w.writerow(["1~20 풀 네 조건", all_ok, by_product, all_ok == by_product])
    print("→ pool_compare.csv 저장 완료")
