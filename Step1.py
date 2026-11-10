"""step1_binarize.py ─ 1단계: 네 조건이 모두 필요할까? (이진화)

1-1. 조건을 빼면(A안, B안) 잘못 허용이 생기는가?
1-2. 검사 순서를 바꾸면 허용·거부 결과가 달라지는가? (16가지 × 24가지 = 384번 판정)
기록: truth_table.csv (진리표), 규칙별 허용 개수 표
"""
import csv
from itertools import product

from config import NAMES, ORDERS, arrow

# ① 16가지 요청 만들기 (수형도와 같은 순서: 0 먼저, 1 나중)
REQUESTS = list(product([0, 1], repeat=4))        # (Q, L, D, T)


def code(r):
    return "".join(map(str, r))


def allow_all(r):
    """올바른 판정: 네 수의 곱. 하나라도 0이면 0(거부)."""
    return r[0] * r[1] * r[2] * r[3]


def judge(r, order):
    """정한 순서로 확인하다가 0이 나오면 그 자리에서 거부.
    돌려주는 값: (허용 1/거부 0, 처음 거부한 문지기)"""
    for k in order:
        if r[NAMES.index(k)] == 0:
            return 0, k
    return 1, "-"


RULES = {
    "A안 (Q만 확인)": ["Q"],
    "B안 (Q·L·D 확인)": ["Q", "L", "D"],
    "C안 (네 조건 모두 확인)": NAMES,
}


def allowed_by(r, conds):
    return int(all(r[NAMES.index(c)] == 1 for c in conds))


if __name__ == "__main__":
    print("=== ①② 16가지 요청 (Q L D T) ===")
    print(f"요청의 종류: {len(REQUESTS)}가지 (= 2×2×2×2)")
    for i, r in enumerate(REQUESTS, 1):
        print(f"{i:2d}. {code(r)}   곱 = {allow_all(r)}")
    print("→ 공책의 수형도에 적은 16가지와 같은지 비교하세요.\n")

    print("=== ③ 규칙별 허용 개수와 잘못 허용 개수 (가설 1-1) ===")
    print(f"{'규칙':<22}{'허용':>6}{'잘못 허용':>10}")
    for name, conds in RULES.items():
        allowed = [r for r in REQUESTS if allowed_by(r, conds)]
        wrong = [r for r in allowed if allow_all(r) == 0]
        print(f"{name:<22}{len(allowed):>6}{len(wrong):>10}   잘못 허용된 요청: "
              f"{', '.join(code(r) for r in wrong) or '없음'}")
    print()

    print("=== ④ 16가지 × 24가지 순서 판정 비교 (가설 1-2) ===")
    total, differ = 0, 0
    for r in REQUESTS:
        results = [judge(r, o)[0] for o in ORDERS]
        total += len(results)
        if len(set(results)) > 1:
            differ += 1
            print(f"  {code(r)}: 순서에 따라 판정이 다름!")
    print(f"비교한 판정 수: {total}번, 순서에 따라 판정이 달라진 요청: {differ}개\n")

    print("=== ⑤ 처음 거부되는 문지기가 순서에 따라 달라지는가? ===")
    with open("truth_table.csv", "w", newline="", encoding="utf-8-sig") as f:
        w = csv.writer(f)
        w.writerow(["요청"] + NAMES + ["곱"] + list(RULES) + [f"처음거부_{arrow(o)}" for o in ORDERS]
                   + ["처음거부_종류수"])
        for r in REQUESTS:
            firsts = [judge(r, o)[1] for o in ORDERS]
            kinds = len(set(firsts))
            w.writerow([code(r)] + list(r) + [allow_all(r)]
                       + [allowed_by(r, c) for c in RULES.values()] + firsts + [kinds])
            if kinds > 1:
                print(f"  {code(r)}: 처음 거부하는 문지기가 {kinds}가지 ({', '.join(sorted(set(firsts)))})")
    print("→ truth_table.csv 저장 완료")
