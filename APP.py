"""app.py ─ QRLOCK 검사 순서 탐구 웹 앱 (Streamlit)

실행 방법:  pip install streamlit pandas numpy matplotlib
           streamlit run app.py
→ 웹 브라우저가 열리면 왼쪽에서
   (1) 실행할 단계와 실행 순서
   (2) 내가 실험할 검사 순서(문지기 4명의 줄 순서)
   (3) 실험 설정(통과 기준, 확인 시간, 요청 수, seed)
   를 정하고 [실행] 버튼을 누른다.
"""
from itertools import product

import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import streamlit as st

from config import (NAMES, FULL, ORDERS, THRESH, COST, arrow, pass_rate, expected_time,
                    rule_order, best_order, make_requests, check_one, measure, set_korean_font)
from step5_envmap import make_env, expected_cost, simulate, mixed_pass

st.set_page_config(page_title="QRLOCK 검사 순서 탐구", page_icon="🔒", layout="wide")
set_korean_font()

STEPS = {
    "1단계 · 이진화": "s1",
    "2단계 · 풀 세기·드문 확률": "s2",
    "3단계 · 24가지 순서 실험": "s3",
    "4단계 · 피팅": "s4",
    "5단계 · 규칙·역전 지점": "s5",
    "6단계 · 검사 순서 지도": "s6",
    "7단계 · QRLOCK 적용": "s7",
}

# ═════════════════════════ 왼쪽 설정 ═════════════════════════
with st.sidebar:
    st.header("① 실행할 단계와 순서")
    st.caption("고른 순서대로 위에서부터 실행됩니다. 빼고 싶은 단계는 ✕로 지우세요.")
    chosen = st.multiselect("단계", list(STEPS), default=list(STEPS), label_visibility="collapsed")

    st.header("② 내가 실험할 검사 순서")
    st.caption("문지기 4명을 줄 세울 순서를 고르세요.")
    mine = [st.selectbox(f"{i + 1}번째 문지기", NAMES, index=i, key=f"pos{i}",
                         format_func=lambda k: f"{k} · {FULL[k]}") for i in range(4)]
    MY = "".join(mine)
    valid = len(set(mine)) == 4
    if valid:
        st.success(f"내 순서: **{arrow(MY)}**")
    else:
        st.error("같은 문지기를 두 번 고를 수 없습니다.")

    st.header("③ 실험 설정 (가상 설정)")
    with st.expander("통과 기준 · 확인 시간", expanded=False):
        th, cost = {}, {}
        for k in NAMES:
            c1, c2 = st.columns(2)
            th[k] = c1.number_input(f"{k} 통과 기준 (1~100)", 1, 100, THRESH[k], key=f"th{k}")
            cost[k] = c2.number_input(f"{k} 확인 시간", 0.0, 20.0, float(COST[k]), 0.5, key=f"c{k}")
    n_main = st.select_slider("3단계 요청 수", [100, 1000, 10000, 100000], value=10000)
    seeds = st.multiselect("seed", list(range(10)), default=[0, 1, 2, 3, 4])
    st.caption("기본값은 계획안 Ⅲ-3의 설정과 같습니다.")
    run = st.button("▶ 실행", type="primary", use_container_width=True, disabled=not (valid and chosen and seeds))

P = pass_rate(th)

st.title("🔒 QRLOCK 검사 순서 탐구")
st.caption("환경이 주어지면, 어떤 검사 순서가 가장 유리할까? ─ 이진화 · 난수 실험 · 피팅으로 만드는 검사 순서 지도")
st.write(" → ".join(f"**{i + 1}.** {s.split(' · ')[0]}" for i, s in enumerate(chosen)) if chosen else "단계를 고르세요.")


def mark_mine(df, col="순서"):
    """표에서 내 순서 줄을 노랗게 표시"""
    return df.style.apply(lambda r: ["background-color: #fff3b0" if r[col] == arrow(MY) else "" for _ in r], axis=1)


def fig_show(fig):
    st.pyplot(fig, clear_figure=True)
    plt.close(fig)


# ═════════════════════════ 1단계 ═════════════════════════
def s1():
    reqs = list(product([0, 1], repeat=4))
    code = lambda r: "".join(map(str, r))

    def judge(r, order):
        for k in order:
            if r[NAMES.index(k)] == 0:
                return 0, k
        return 1, "-"

    st.markdown("**1-1. 조건을 빼면 잘못 허용이 생길까?**")
    rules = {"A안 (Q만)": ["Q"], "B안 (Q·L·D)": ["Q", "L", "D"], "C안 (네 조건 모두)": NAMES}
    rows = []
    for name, conds in rules.items():
        allowed = [r for r in reqs if all(r[NAMES.index(c)] for c in conds)]
        wrong = [r for r in allowed if r[0] * r[1] * r[2] * r[3] == 0]
        rows.append([name, len(allowed), len(wrong), ", ".join(map(code, wrong)) or "없음"])
    st.dataframe(pd.DataFrame(rows, columns=["규칙", "허용", "잘못 허용", "잘못 허용된 요청"]), hide_index=True)

    st.markdown("**1-2. 순서를 바꾸면 판정이 달라질까?**")
    differ = sum(len({judge(r, o)[0] for o in ORDERS}) > 1 for r in reqs)
    st.write(f"16가지 × 24가지 = **{16 * 24}번** 판정 비교 → 순서에 따라 판정이 달라진 요청: **{differ}개**")

    st.markdown(f"**진리표** (내 순서 {arrow(MY)}에서 처음 거부하는 문지기 포함)")
    tt = pd.DataFrame([{"요청": code(r), **dict(zip(NAMES, r)), "곱": r[0] * r[1] * r[2] * r[3],
                        f"처음 거부 ({arrow(MY)})": judge(r, MY)[1],
                        "처음 거부 종류 수 (24가지 순서)": len({judge(r, o)[1] for o in ORDERS})} for r in reqs])
    st.dataframe(tt, hide_index=True)
    st.download_button("truth_table.csv 내려받기", tt.to_csv(index=False).encode("utf-8-sig"), "truth_table.csv")


# ═════════════════════════ 2단계 ═════════════════════════
@st.cache_data
def rare_experiment(trials, seeds, pool=20000):
    rows = []
    for n in trials:
        for s in seeds:
            hits = int((np.random.default_rng(s).integers(1, pool + 1, size=n) == 1).sum())
            rows.append([n, s, hits, hits / n, 0.00004 <= hits / n <= 0.00006])
    return pd.DataFrame(rows, columns=["실험 횟수", "seed", "맞힌 횟수", "실험 확률", "0.00004~0.00006 안"])


def s2():
    c1, c2 = st.columns(2)
    with c1:
        st.markdown("**모눈종이 넓이 모델**")
        a = st.slider("가로 10칸 중 만족하는 칸", 1, 10, 6)
        b = st.slider("세로 10칸 중 만족하는 칸", 1, 10, 7)
        grid = np.zeros((10, 10))
        grid[:b, :a] = 1
        fig, ax = plt.subplots(figsize=(3.2, 3.2))
        ax.imshow(grid, cmap="Blues", origin="lower", vmin=0, vmax=1.4)
        ax.set_xticks(np.arange(-.5, 10), []); ax.set_yticks(np.arange(-.5, 10), [])
        ax.grid(color="gray", lw=0.5)
        ax.set_title(f"{a} × {b} = {a * b}칸 / 100칸")
        fig_show(fig)
    with c2:
        st.markdown("**1~20 풀에서 160,000가지 직접 세기 (2-1)**")
        lim = {k: st.number_input(f"{k}: 1~20 중 이 수 이하이면 만족", 1, 20, v, key=f"lim{k}")
               for k, v in {"Q": 12, "L": 14, "D": 16, "T": 19}.items()}
        v = np.arange(1, 21)
        Qg, Lg, Dg, Tg = np.meshgrid(v, v, v, v, indexing="ij")     # 160,000가지 조합 전부
        counted = int(((Qg <= lim["Q"]) & (Lg <= lim["L"]) & (Dg <= lim["D"]) & (Tg <= lim["T"])).sum())
        prod_ = lim["Q"] * lim["L"] * lim["D"] * lim["T"]
        st.write(f"직접 센 개수: **{counted:,}**  /  곱한 개수: "
                 f"{'×'.join(str(lim[k]) for k in NAMES)} = **{prod_:,}** → {'같다' if counted == prod_ else '다르다'}")

    st.markdown("**드문 확률 실험: 풀 20,000개 중 1개 맞히기 (2-2)**")
    trials = st.multiselect("실험 횟수", [10_000, 100_000, 1_000_000, 2_000_000],
                            default=[10_000, 100_000, 1_000_000, 2_000_000])
    rseeds = st.multiselect("seed (2-2)", list(range(10)), default=[0, 1, 2])
    if trials and rseeds:
        df = rare_experiment(tuple(sorted(trials)), tuple(rseeds))
        st.dataframe(df.style.format({"실험 확률": "{:.6f}", "실험 횟수": "{:,}"}), hide_index=True)


# ═════════════════════════ 3단계 ═════════════════════════
def s3():
    st.markdown(f"**요청 1건을 내 순서 {arrow(MY)}로 검사해 보기**")
    demo_seed = st.number_input("요청을 만들 seed", 0, 9999, 0)
    req = make_requests(1, demo_seed, th)[0]
    log = []
    total = 0
    for k in MY:
        total += cost[k]
        ok = req[NAMES.index(k)]
        log.append([k, FULL[k], cost[k], total, "통과" if ok else "실패 → 거부"])
        if not ok:
            break
    st.write("요청:", "".join(map(str, req)), "(Q L D T, 1 = 통과)")
    st.dataframe(pd.DataFrame(log, columns=["문지기", "조건", "확인 시간", "누적", "결과"]), hide_index=True)

    up = st.file_uploader("1차 탐구 요청 100건 CSV (Q,L,D,T 열, 0/1) ─ 선택", type="csv")
    if up is not None:
        r100 = pd.read_csv(up)[NAMES].to_numpy()
        ones = {k: 1 for k in NAMES}
        st.dataframe(mark_mine(pd.DataFrame([[arrow(o), round(measure(o, r100, ones) * len(r100))] for o in ORDERS],
                                            columns=["순서", "확인 횟수"])), hide_index=True)

    st.markdown(f"**요청 {n_main:,}건 × 24가지 순서** (같은 요청을 24가지 순서에 똑같이 적용)")
    tabs = st.tabs([f"seed {s}" for s in seeds])
    tops = []
    for tab, s in zip(tabs, seeds):
        reqs = make_requests(n_main, s, th)
        res = {o: measure(o, reqs, cost) for o in ORDERS}
        ranked = sorted(ORDERS, key=res.get)
        tops.append([s] + [arrow(o) for o in ranked[:3]] + [ranked.index(MY) + 1])
        with tab:
            df = pd.DataFrame([[i + 1, arrow(o), res[o]] for i, o in enumerate(ranked)],
                              columns=["순위", "순서", "평균 확인 시간"])
            st.dataframe(mark_mine(df).format({"평균 확인 시간": "{:.4f}"}), hide_index=True, height=300)
            st.caption(f"서로 다른 평균 확인 시간: {len({round(v, 9) for v in res.values()})}가지")
    st.markdown("**seed별 1~3위와 내 순서의 순위**")
    st.dataframe(pd.DataFrame(tops, columns=["seed", "1위", "2위", "3위", f"{arrow(MY)} 순위"]), hide_index=True)


# ═════════════════════════ 4단계 ═════════════════════════
def s4():
    st.markdown(f"**① 내 순서 {arrow(MY)}의 표 계산 (요청 10,000건)**")
    alive, rows, total = 10000, [], 0
    for k in MY:
        rows.append([k, alive, cost[k], alive * cost[k], alive * P[k]])
        total += alive * cost[k]
        alive *= P[k]
    st.dataframe(pd.DataFrame(rows, columns=["문지기", "확인받는 요청", "1건 확인 시간", "걸린 시간 합", "다음으로 가는 요청"])
                 .style.format("{:,.0f}", subset=["확인받는 요청", "걸린 시간 합", "다음으로 가는 요청"]), hide_index=True)
    st.write(f"합계 {total:,.0f} → 1건당 **{total / 10000:.4f}**  (계산식 함수: {expected_time(MY, P, cost):.4f})")

    sizes = [100, 1000, 10000, 100000]
    calc = {o: expected_time(o, P, cost) for o in ORDERS}
    errs, pts = {}, []
    for n in sizes:
        e = []
        for s in seeds:
            reqs = make_requests(n, s, th)
            for o in ORDERS:
                v = measure(o, reqs, cost)
                e.append(abs(v - calc[o]))
                if n == 10000:
                    pts.append((calc[o], v, o == MY))
        errs[n] = np.mean(e)

    c1, c2 = st.columns(2)
    with c1:
        fig, ax = plt.subplots(figsize=(5, 5))
        x = [p[0] for p in pts]; y = [p[1] for p in pts]
        ax.scatter(x, y, s=16, alpha=.5, label="24가지 순서 × seed")
        ax.scatter([p[0] for p in pts if p[2]], [p[1] for p in pts if p[2]], s=40, c="red", label=f"내 순서 {arrow(MY)}")
        lo, hi = min(x + y) - .1, max(x + y) + .1
        ax.plot([lo, hi], [lo, hi], "k--", lw=1, label="y = x")
        ax.set_xlabel("계산값"); ax.set_ylabel("실험값"); ax.set_title("계산값과 실험값 (요청 10,000건)"); ax.legend()
        fig_show(fig)
        st.write(f"요청 10,000건 평균 오차: **{errs[10000]:.4f}** (판단 기준 0.05 이하)")
    with c2:
        ns, es = np.array(sizes), np.array([errs[n] for n in sizes])
        slope, inter = np.polyfit(np.log10(ns), np.log10(es), 1)
        fig, ax = plt.subplots(figsize=(5, 5))
        ax.loglog(ns, es, "o", label="평균 오차")
        ax.loglog(ns, 10 ** inter * ns ** slope, "-", label=f"맞춘 직선 (기울기 {slope:.2f})")
        ax.set_xlabel("요청 수"); ax.set_ylabel("평균 오차"); ax.set_title("요청 수에 따른 오차"); ax.legend()
        fig_show(fig)
        st.write(f"기울기: **{slope:.3f}** (판단 기준 −0.6 ~ −0.4) → 요청 100배일 때 오차 약 {100 ** slope:.3f}배")


# ═════════════════════════ 5단계 ═════════════════════════
def s5():
    st.markdown("**① 이웃한 두 문지기 바꾸기**")
    c1, c2 = st.columns(2)
    X = c1.selectbox("문지기 X", NAMES, 0)
    Y = c2.selectbox("문지기 Y", NAMES, 2)
    if X != Y:
        xf, yf = cost[X] + P[X] * cost[Y], cost[Y] + P[Y] * cost[X]
        st.write(f"{X} 먼저: {cost[X]} + {P[X]}×{cost[Y]} = **{xf:.3f}**  |  "
                 f"{Y} 먼저: {cost[Y]} + {P[Y]}×{cost[X]} = **{yf:.3f}**  → "
                 f"**{X if xf < yf else Y if yf < xf else '같음'}** 이(가) 앞")

    st.markdown("**② 문지기별 '확인 시간 ÷ 거부 비율'**")
    st.dataframe(pd.DataFrame([[k, cost[k], 1 - P[k], cost[k] / (1 - P[k]) if P[k] < 1 else np.inf] for k in NAMES],
                              columns=["문지기", "확인 시간", "거부 비율", "시간 ÷ 거부 비율"]), hide_index=True)
    rule = rule_order(P, cost)
    best, res = best_order(P, cost)
    st.write(f"규칙 순서 **{arrow(rule)}** ({res[rule]:.4f}) / 24가지 1위 **{arrow(best)}** ({res[best]:.4f}) / "
             f"내 순서 {arrow(MY)} ({res[MY]:.4f}, {sorted(ORDERS, key=res.get).index(MY) + 1}위)")

    st.markdown("**③ 한 문지기의 통과 기준을 바꾸면 순서는 언제 뒤바뀔까? (5-2)**")
    c1, c2, c3 = st.columns(3)
    G = c1.selectbox("바꿀 문지기", NAMES, 0)
    oA = c2.selectbox("비교 순서 A", ORDERS, ORDERS.index("QDLT"), format_func=arrow)
    oB = c3.selectbox("비교 순서 B", ORDERS, ORDERS.index("DQLT"), format_func=arrow)
    qs = np.arange(10, 100, 10)
    rows, yA, yB = [], [], []
    for q in qs:
        th2 = dict(th, **{G: int(q)})
        p2 = pass_rate(th2)
        rs = [make_requests(10000, s, th2) for s in seeds]
        yA.append(np.mean([measure(oA, r, cost) for r in rs]))
        yB.append(np.mean([measure(oB, r, cost) for r in rs]))
        rows.append([q / 100, arrow(best_order(p2, cost)[0]), arrow(rule_order(p2, cost))])
    st.dataframe(pd.DataFrame(rows, columns=[f"{G} 통과율", "계산 1위", "규칙 순서"]), hide_index=True)
    x = qs / 100
    a1, b1 = np.polyfit(x, yA, 1)
    a2, b2 = np.polyfit(x, yB, 1)
    fig, ax = plt.subplots(figsize=(7, 4))
    ax.plot(x, yA, "o", c="C0", label=f"{arrow(oA)} 실험"); ax.plot(x, a1 * x + b1, c="C0")
    ax.plot(x, yB, "s", c="C1", label=f"{arrow(oB)} 실험"); ax.plot(x, a2 * x + b2, c="C1")
    if abs(a1 - a2) > 1e-12:
        cross = (b2 - b1) / (a1 - a2)
        # 계산식으로 예측한 교점: 두 순서의 계산값 직선(통과율 0과 1에서의 값으로 결정)이 만나는 곳
        fA = lambda q: expected_time(oA, dict(P, **{G: q}), cost)
        fB = lambda q: expected_time(oB, dict(P, **{G: q}), cost)
        ca, cb = fA(1) - fA(0), fB(1) - fB(0)
        pred = (fB(0) - fA(0)) / (ca - cb) if abs(ca - cb) > 1e-12 else np.nan
        ax.axvline(cross, ls="--", c="gray")
        st.write(f"실험 직선의 교점: **{cross:.4f}**  /  계산으로 예측한 지점: **{pred:.4f}**  /  차이 {abs(cross - pred):.4f}"
                 f" (판단 기준 ±0.05)")
    else:
        st.write("두 직선이 평행해서 교점이 없습니다.")
    ax.set_xlabel(f"{G} 통과율"); ax.set_ylabel("평균 확인 시간"); ax.legend()
    fig_show(fig)


# ═════════════════════════ 6단계 ═════════════════════════
@st.cache_data
def envmap(my, cost_items):
    c = dict(cost_items)
    Ks = [1, 2, 3, 4, 5, 7, 10, 15, 20, 30, 50, 100]
    Ws = np.round(np.arange(0.05, 1.0001, 0.05), 2)
    best = [[None] * len(Ks) for _ in Ws]
    gain = np.zeros((len(Ws), len(Ks)))
    mygain = np.zeros_like(gain)
    rule_same = my_first = 0
    for i, w in enumerate(Ws):
        for j, K in enumerate(Ks):
            env = make_env(K=K, w=w)
            res = {o: expected_cost(o, env, c) for o in ORDERS}
            b = min(res, key=res.get)
            best[i][j] = b
            gain[i, j] = 100 * (1 - res[b] / res["LQDT"])
            mygain[i, j] = 100 * (1 - res[my] / res["LQDT"])
            rule_same += abs(res[rule_order(mixed_pass(env), c)] - res[b]) < 1e-12
            my_first += abs(res[my] - res[b]) < 1e-12
    return Ks, Ws, best, gain, mygain, rule_same, my_first


def s6():
    Ks, Ws, best, gain, mygain, rule_same, my_first = envmap(MY, tuple(cost.items()))
    kinds = sorted({b for row in best for b in row})
    idx = np.array([[kinds.index(b) for b in row] for row in best])
    fig, ax = plt.subplots(1, 3, figsize=(19, 5.2))
    im = ax[0].imshow(idx, origin="lower", aspect="auto", cmap=plt.get_cmap("tab10", len(kinds)),
                      vmin=-.5, vmax=len(kinds) - .5)
    bar = fig.colorbar(im, ax=ax[0], ticks=range(len(kinds)))
    bar.ax.set_yticklabels([arrow(k) for k in kinds])
    for a_, data, t in [(ax[1], gain, "1위 순서: 현재 L→Q→D→T 대비 절감률"),
                        (ax[2], mygain, f"내 순서 {arrow(MY)}: 현재 대비 절감률")]:
        im2 = a_.imshow(data, origin="lower", aspect="auto", cmap="viridis")
        fig.colorbar(im2, ax=a_, label="절감률 (%)")
        a_.set_title(t)
    ax[0].set_title("환경별 1위 검사 순서")
    for a_ in ax:
        a_.set_xticks(range(len(Ks))); a_.set_xticklabels(Ks)
        a_.set_yticks(range(0, len(Ws), 2)); a_.set_yticklabels([f"{x:.0%}" for x in Ws[::2]])
        a_.set_xlabel("택배 기사 수 K"); a_.set_ylabel("열람 가능 시간 비율 w")
    plt.tight_layout()
    fig_show(fig)

    n = len(Ks) * len(Ws)
    lq = sum(row.count("LQDT") for row in best)
    st.dataframe(pd.DataFrame([[arrow(k), sum(row.count(k) for row in best)] for k in kinds],
                              columns=["1위 순서", "칸 수"]), hide_index=True)
    st.write(f"현재 순서 L→Q→D→T가 1위인 칸: **{lq} / {n}** (6-2)  ·  규칙 순서 = 1위인 칸: **{rule_same} / {n}** (6-3)  ·  "
             f"내 순서가 1위(같은 시간 포함)인 칸: **{my_first} / {n}**")

    st.markdown("**한 칸 골라 계산과 난수 실험 비교**")
    c1, c2, c3 = st.columns(3)
    K = c1.selectbox("기사 수 K", Ks, Ks.index(10))
    w = c2.selectbox("열람 가능 시간 비율 w", list(Ws), list(Ws).index(0.3), format_func=lambda x: f"{x:.0%}")
    nn = c3.select_slider("실험 요청 수", [10000, 100000], 100000)
    env = make_env(K=K, w=w)
    res = {o: expected_cost(o, env, cost) for o in ORDERS}
    b = min(res, key=res.get)
    show = list(dict.fromkeys([b, MY, "LQDT"]))
    st.dataframe(pd.DataFrame([[arrow(o), res[o], simulate(o, env, nn, cost=cost)] for o in show],
                              columns=["순서", "계산", "실험"]).style.format({"계산": "{:.3f}", "실험": "{:.3f}"}),
                 hide_index=True)


# ═════════════════════════ 7단계 ═════════════════════════
def s7():
    L_ORDERS = [o for o in ORDERS if o[0] == "L"]
    rest = [k for k in NAMES if k != "L"]
    st.write(f"L로 시작하는 순서: **{len(L_ORDERS)}가지** (수형도 3×2×1 = 6)  ─  " + ", ".join(arrow(o) for o in L_ORDERS))
    model = st.radio("모형", ["단순 모형", "2층 모형"], horizontal=True)
    if model == "2층 모형":
        c1, c2 = st.columns(2)
        K = c1.number_input("기사 수 K", 1, 1000, 10)
        w = c2.slider("열람 가능 시간 비율 w", 0.05, 1.0, 0.3, 0.05)
        env = make_env(K=K, w=w)
    keep = dict(cost, L=0)
    rows = []
    for c_, label in [(cost, "로그인 매번"), (keep, "로그인 유지 (L = 0)")]:
        for o in L_ORDERS:
            if model == "단순 모형":
                calc = expected_time(o, P, c_)
                exp = np.mean([measure(o, make_requests(10000, s, th), c_) for s in seeds])
            else:
                calc, exp = expected_cost(o, env, c_), simulate(o, env, 100000, cost=c_)
            rows.append([label, arrow(o), calc, exp])
    df = pd.DataFrame(rows, columns=["상황", "순서", "계산", "실험"])
    st.dataframe(mark_mine(df).format({"계산": "{:.4f}", "실험": "{:.4f}"}), hide_index=True)

    if model == "단순 모형":
        rule = "L" + rule_order(P, cost, rest)
    else:   # 뒤 세 문지기는 L을 통과한 요청만 만나므로 그 안에서의 통과율로 규칙 적용
        pl = sum(r * p["L"] for r, p in env)
        rule = "L" + rule_order({k: sum(r * p["L"] * p[k] for r, p in env) / pl for k in rest}, cost, rest)
    before = df[df["상황"] == "로그인 매번"].set_index("순서")["계산"]
    after = df[df["상황"] != "로그인 매번"].set_index("순서")["계산"]
    st.write(f"L 고정 1위: **{before.idxmin()}**  /  규칙으로 정한 순서: **{arrow(rule)}**  → "
             f"{'같은 시간' if abs(before[arrow(rule)] - before.min()) < 1e-12 else '다름'} (7-1)")
    cur = before["L→Q→D→T"]
    st.write(f"현재 L→Q→D→T {cur:.4f} → L 고정 1위 {before.min():.4f} ({100 * (1 - before.min() / cur):.2f}% 절감) → "
             f"로그인 유지 1위 {after.min():.4f} ({100 * (1 - after.min() / cur):.2f}% 절감) (7-2)")


# ═════════════════════════ 실행 ═════════════════════════
if run:
    st.session_state["ran"] = True
if st.session_state.get("ran") and valid:
    for i, name in enumerate(chosen, 1):
        st.divider()
        st.subheader(f"{i}. {name}")
        globals()[STEPS[name]]()
    st.divider()
    st.caption("※ 모든 값은 탐구를 위해 정한 가상 설정에서 나온 결과입니다. 가설 판정은 직접 실행한 결과로 기록하세요.")
else:
    st.info("왼쪽에서 단계·순서·설정을 정하고 **▶ 실행**을 누르세요.")
