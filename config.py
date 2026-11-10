"""config.py ─ 모든 단계에서 함께 쓰는 설정값, 세어서 구한 확률, 평균 시간 계산식

※ 아래 값은 실제 운영 자료가 아니라 탐구를 위해 정한 가상 설정이다. (계획안 Ⅲ-3)
"""
from itertools import permutations

import numpy as np

# ── 문지기(조건) ────────────────────────────────────────────
NAMES = ["Q", "L", "D", "T"]
FULL = {"Q": "QR 인증정보 일치", "L": "로그인 성공", "D": "담당 기사 일치", "T": "열람시간 유효"}
ORDERS = ["".join(p) for p in permutations(NAMES)]      # 4×3×2×1 = 24가지 순서

# ── 단순 모형 (3~5단계) ─────────────────────────────────────
THRESH = {"Q": 60, "L": 70, "D": 80, "T": 95}           # 1~100 중 기준 이하이면 통과
COST = {"Q": 3, "L": 5, "D": 1, "T": 1}                 # 1건 확인 시간 (단위 없는 상대값)
SIZES = [100, 1000, 10000, 100000]                      # 요청 수
SEEDS = [0, 1, 2, 3, 4]                                 # 반복 (seed 0~4)


def arrow(order):
    """'QLDT' → 'Q→L→D→T'"""
    return "→".join(order)


def pass_rate(thresh=THRESH):
    """세어서 구한 통과 확률 = (기준 이하인 수의 개수) ÷ 100"""
    return {k: thresh[k] / 100 for k in NAMES}


def expected_time(order, p, cost=COST):
    """계산식: 평균 확인 시간 = Σ (앞을 모두 통과한 비율 × 그 문지기의 확인 시간)"""
    total, alive = 0.0, 1.0
    for k in order:
        total += alive * cost[k]
        alive *= p[k]
    return total


def rule_order(p, cost=COST, names=NAMES):
    """규칙(가설 5-1): '확인 시간 ÷ 거부 비율'이 작은 문지기부터 세운다.
    아무도 거부하지 않는 문지기(거부 비율 0)는 맨 뒤로 보낸다."""
    def key(k):
        reject = 1 - p[k]
        return cost[k] / reject if reject > 0 else float("inf")
    return "".join(sorted(names, key=key))


def best_order(p, cost=COST, orders=ORDERS):
    """주어진 순서를 모두 계산해 가장 빠른 순서를 찾는다 (완전 탐색)."""
    res = {o: expected_time(o, p, cost) for o in orders}
    return min(res, key=res.get), res


# ── 난수 실험 ──────────────────────────────────────────────
def make_requests(n, seed, thresh=THRESH):
    """가상 요청 n건: 조건마다 1~100 중 하나를 뽑아 기준 이하이면 1(통과), 아니면 0(실패).
    결과는 n줄 × 4칸(Q L D T 순서) 표이다."""
    rng = np.random.default_rng(seed)
    draws = rng.integers(1, 101, size=(n, 4))
    limits = np.array([thresh[k] for k in NAMES])
    return (draws <= limits).astype(int)


def check_one(request, order, cost=COST, verbose=False):
    """요청 1건을 한 순서로 검사한다 (손 계산과 비교하는 용도).
    돌려주는 값: (걸린 시간 합, 거부한 문지기 또는 None)"""
    total = 0
    for k in order:
        total += cost[k]
        ok = request[NAMES.index(k)]
        if verbose:
            print(f"  {k}({FULL[k]}) 확인: +{cost[k]} → 누적 {total}, {'통과' if ok else '실패 → 거부'}")
        if ok == 0:
            return total, k
    return total, None


def measure(order, req, cost=COST):
    """요청 여러 건을 한 순서로 검사한 평균 확인 시간 (실험값).
    앞 문지기를 통과한 요청(alive)만 다음 문지기에게 확인을 받는다."""
    alive = np.ones(len(req), dtype=bool)
    total = 0
    for k in order:
        total += cost[k] * alive.sum()
        alive &= req[:, NAMES.index(k)] == 1
    return total / len(req)


# ── 그래프 한글 글꼴 ────────────────────────────────────────
def set_korean_font():
    import matplotlib.pyplot as plt
    from matplotlib import font_manager
    have = {f.name for f in font_manager.fontManager.ttflist}
    for name in ["Malgun Gothic", "AppleGothic", "NanumGothic", "Noto Sans CJK KR", "Noto Sans KR"]:
        if name in have:
            plt.rcParams["font.family"] = name
            break
    else:
        print("※ 한글 글꼴을 찾지 못했습니다. 그래프의 한글이 네모로 보일 수 있습니다.")
    plt.rcParams["axes.unicode_minus"] = False


if __name__ == "__main__":
    print("24가지 순서:", ", ".join(arrow(o) for o in ORDERS))
    p = pass_rate()
    print("통과 확률:", p)
    print("Q→L→D→T 평균 확인 시간(계산):", expected_time("QLDT", p))
