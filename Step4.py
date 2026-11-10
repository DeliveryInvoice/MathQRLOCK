"""step2_test.py ─ 3단계(24가지 순서 실험)와 5단계(Q 통과 기준 바꾸기 실험)

① 요청 1건 만들기  ② 요청 1건을 한 순서로 검사 → 손 계산과 비교
③ 1차 탐구의 요청 100건 확인 (first_study_100.csv 가 있을 때)
④⑤ 요청 100~100,000건 × seed 0~4 로 24가지 순서 실험 → results.csv
5단계 ⑤ Q 통과 기준 10, 20, …, 90 → threshold_results.csv
"""
import csv
import os

import numpy as np

from config import (NAMES, ORDERS, THRESH, SIZES, SEEDS, arrow, pass_rate,
                    expected_time, make_requests, check_one, measure)


def demo_one():
    print("=== ① 요청 1건 만들기 ===")
    req = make_requests(1, seed=0)[0]
    print("요청:", "".join(map(str, req)), "  (Q L D T 순서, 1 = 통과, 0 = 실패)")
    print("\n=== ② 요청 1건을 Q→L→D→T로 검사 ===")
    t, who = check_one(req, "QLDT", verbose=True)
    print(f"걸린 시간 합: {t}  ({'허용' if who is None else who + '에서 거부'})")
    print("→ 공책에 손으로 계산한 값과 같은지 확인하세요.")


def check_first_study(path="first_study_100.csv"):
    print("\n=== ③ 1차 탐구 요청 100건 확인 ===")
    if not os.path.exists(path):
        print(f"'{path}' 파일이 없어 건너뜁니다.")
        print("  1차 탐구의 요청 100건을 Q,L,D,T 네 열(0 또는 1)로 저장해 두면 순서별 확인 횟수를 출력합니다.")
        return
    with open(path, encoding="utf-8-sig") as f:
        req = np.array([[int(r[k]) for k in NAMES] for r in csv.DictReader(f)])
    ones = {k: 1 for k in NAMES}           # 확인 '횟수'를 세므로 확인 시간을 모두 1로
    for o in ORDERS:
        print(f"  {arrow(o)}: {round(measure(o, req, ones) * len(req))}회")
    print("→ 1차 탐구에서 얻은 횟수(200회, 315회)가 그대로 나오는지 확인하세요.")


def run_main(out="results.csv"):
    print("\n=== ④⑤ 24가지 순서 실험 (요청 수 × seed) ===")
    p = pass_rate()
    rows = []
    for n in SIZES:
        for s in SEEDS:
            req = make_requests(n, s)                    # 같은 요청을 24가지 순서에 똑같이 적용
            res = {o: measure(o, req) for o in ORDERS}
            ranked = sorted(ORDERS, key=res.get)
            for o in ORDERS:
                rows.append([n, s, o, res[o], expected_time(o, p), ranked.index(o) + 1])

    with open(out, "w", newline="", encoding="utf-8-sig") as f:
        w = csv.writer(f)
        w.writerow(["요청수", "seed", "순서", "실험값", "계산값", "순위"])
        w.writerows(rows)

    # 요청 10,000건, seed 0 순위표
    sub = sorted([r for r in rows if r[0] == 10000 and r[1] == 0], key=lambda r: r[5])
    print("요청 10,000건, seed 0 의 24가지 순서 순위표")
    print(f"{'순위':>4}  {'순서':<10}{'평균 확인 시간':>14}")
    for r in sub:
        print(f"{r[5]:>4}  {arrow(r[2]):<10}{r[3]:>14.4f}")
    print(f"서로 다른 평균 확인 시간의 개수: {len({round(r[3], 9) for r in sub})}가지 (가설 3-1)")
    q_rank = next(r[5] for r in sub if r[2] == "QLDT")
    print(f"Q→L→D→T 의 순위: {q_rank}위 (가설 3-2)")

    print("\nseed별 1~3위 (요청 10,000건)")
    for s in SEEDS:
        top = sorted([r for r in rows if r[0] == 10000 and r[1] == s], key=lambda r: r[5])[:3]
        print(f"  seed {s}: " + " / ".join(f"{arrow(r[2])}({r[3]:.4f})" for r in top))
    print(f"→ {out} 저장 완료")


def run_threshold(out="threshold_results.csv", n=10000):
    print("\n=== 5단계 ⑤ Q 통과 기준 바꾸기 (요청 10,000건, seed 0~4) ===")
    rows = []
    for q in range(10, 100, 10):
        th = dict(THRESH, Q=q)
        p = pass_rate(th)
        calc_best = min(ORDERS, key=lambda o: expected_time(o, p))
        for s in SEEDS:
            req = make_requests(n, s, th)
            res = {o: measure(o, req) for o in ORDERS}
            best = min(res, key=res.get)
            rows.append([q, s, best, res["QDLT"], res["DQLT"],
                         expected_time("QDLT", p), expected_time("DQLT", p), calc_best])

    with open(out, "w", newline="", encoding="utf-8-sig") as f:
        w = csv.writer(f)
        w.writerow(["Q기준", "seed", "실험1위", "QDLT_실험", "DQLT_실험",
                    "QDLT_계산", "DQLT_계산", "계산1위"])
        w.writerows(rows)

    print(f"{'Q 통과율':>8}  {'seed 0~4 실험 1위':<52}{'계산 1위'}")
    for q in range(10, 100, 10):
        sub = [r for r in rows if r[0] == q]
        print(f"{q / 100:>8.1f}  {', '.join(arrow(r[2]) for r in sub):<52}{arrow(sub[0][7])}")
    print(f"→ {out} 저장 완료")


if __name__ == "__main__":
    demo_one()
    check_first_study()
    run_main()
    run_threshold()
