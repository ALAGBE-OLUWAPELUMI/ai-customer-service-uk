"""
analyze.py — AI in customer service and consumer outcomes in UK telecoms and utilities.

Three sources:
  * app reviews with an AI-mention flag  -> is AI-channel service rated worse?
  * Ofcom complaints per 100,000 (telecoms, 2010-2025) -> long-run consumer outcome
  * Citizens Advice energy panel -> do complaints track service responsiveness?

Run:  python prepare_data.py && python analyze.py
"""
import os, json
import numpy as np
import pandas as pd
import statsmodels.formula.api as smf
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import data as D

FIG = "outputs/figures"; TAB = "outputs/tables"
os.makedirs(FIG, exist_ok=True); os.makedirs(TAB, exist_ok=True)
plt.rcParams.update({"figure.dpi": 120, "font.size": 10, "axes.grid": True,
                     "grid.alpha": .3, "axes.spines.top": False, "axes.spines.right": False})
NAVY = "#1F3864"; ORANGE = "#C55A11"; TEAL = "#2E75B6"; GREY = "#7F7F7F"


def main():
    rv = D.load_reviews(); ca = D.load_ca(); of = D.load_ofcom()
    M = {}

    # ---------- Reviews: is the AI channel rated worse? ----------
    rv["ai_related"] = rv["ai_related"].astype(bool)
    M["reviews_n"] = int(len(rv))
    M["ai_share"] = round(float(rv.ai_related.mean()), 3)
    m_ai = float(rv[rv.ai_related].score.mean()); m_non = float(rv[~rv.ai_related].score.mean())
    M["mean_score_ai"] = round(m_ai, 3); M["mean_score_nonai"] = round(m_non, 3)
    M["ai_gap_raw"] = round(m_non - m_ai, 3)
    reg = smf.ols("score ~ ai_related + C(brand) + C(year)", rv).fit()
    M["ai_coef_adjusted"] = round(float(reg.params.get("ai_related[T.True]", np.nan)), 3)
    M["ai_coef_p"] = float(reg.pvalues.get("ai_related[T.True]", np.nan))

    g = rv.groupby(["brand", "ai_related"]).score.mean().unstack()
    g.to_csv(f"{TAB}/reviews_ai_by_brand.csv")
    fig, ax = plt.subplots(figsize=(8, 5))
    idx = np.arange(len(g)); w = 0.38
    ax.bar(idx - w/2, g[False], w, label="Other reviews", color=NAVY)
    ax.bar(idx + w/2, g[True], w, label="Mentions AI", color=ORANGE)
    ax.set_xticks(idx); ax.set_xticklabels([b.replace("_", " ") for b in g.index], rotation=20, ha="right")
    ax.set_ylabel("Mean star rating"); ax.set_ylim(0, 5)
    ax.set_title("Reviews that mention AI are rated lower at four of the five brands")
    ax.legend(); fig.tight_layout(); fig.savefig(f"{FIG}/fig1_reviews_ai_by_brand.png"); plt.close(fig)

    # ---------- Ofcom: long-run telecoms complaints ----------
    of["yearf"] = of["year"] + (of["q"] - 1) / 4.0
    ia = of[of.is_industry_avg].copy()
    fig, ax = plt.subplots(figsize=(8, 5))
    for svc, c in zip(["Fixed broadband", "Landline", "Pay-monthly mobile", "Pay TV"], [NAVY, ORANGE, TEAL, GREY]):
        d = ia[ia.service == svc].sort_values("yearf")
        if len(d): ax.plot(d.yearf, d.complaints_per_100k, label=svc, color=c, lw=1.8)
    ax.set_xlabel("Year"); ax.set_ylabel("Complaints per 100,000 (industry average)")
    ax.set_title("UK telecoms complaints fell over 2010 to 2025")
    ax.legend(); fig.tight_layout(); fig.savefig(f"{FIG}/fig2_ofcom_trend.png"); plt.close(fig)
    bb = ia[ia.service == "Fixed broadband"].sort_values("yearf")
    if len(bb):
        M["broadband_avg_first"] = float(bb.iloc[0].complaints_per_100k)
        M["broadband_avg_last"] = float(bb.iloc[-1].complaints_per_100k)

    late = of[(of.year == 2025) & (of.q == 4) & (of.service == "Fixed broadband") & (~of.is_industry_avg)].sort_values("complaints_per_100k")
    late.to_csv(f"{TAB}/ofcom_broadband_q4_2025.csv", index=False)
    fig, ax = plt.subplots(figsize=(7, 5))
    ax.barh([p.replace(" Group", "") for p in late.provider], late.complaints_per_100k, color=NAVY)
    ax.set_xlabel("Complaints per 100,000, Q4 2025"); ax.set_title("Fixed broadband complaints by provider, Q4 2025")
    fig.tight_layout(); fig.savefig(f"{FIG}/fig3_ofcom_latest_broadband.png"); plt.close(fig)

    # ---------- Citizens Advice energy: complaints vs service responsiveness ----------
    d = ca.dropna(subset=["complaints_per_10k", "call_wait_s"]).copy()
    M["ca_reg_n"] = int(len(d))
    try:
        r2 = smf.ols("complaints_per_10k ~ call_wait_s + C(supplier) + C(year)", d).fit()
        M["ca_callwait_coef"] = round(float(r2.params.get("call_wait_s", np.nan)), 4)
        M["ca_callwait_p"] = float(r2.pvalues.get("call_wait_s", np.nan))
    except Exception as e:
        M["ca_callwait_coef"] = None
    cc = ca.dropna(subset=["complaints_per_10k", "star_rating"]).copy()
    M["ca_star_complaints_corr"] = round(float(cc.star_rating.corr(cc.complaints_per_10k)), 3)
    fig, ax = plt.subplots(figsize=(7, 5))
    ax.scatter(cc.star_rating, cc.complaints_per_10k, alpha=.4, color=NAVY, edgecolor="none")
    b, a = np.polyfit(cc.star_rating, cc.complaints_per_10k, 1)
    xs = np.linspace(cc.star_rating.min(), cc.star_rating.max(), 50)
    ax.plot(xs, a + b*xs, color=ORANGE, lw=2)
    ax.set_xlabel("Overall star rating"); ax.set_ylabel("Complaints per 10,000 customers")
    ax.set_title(f"Energy: higher rated suppliers get fewer complaints (r = {M['ca_star_complaints_corr']})")
    fig.tight_layout(); fig.savefig(f"{FIG}/fig4_ca_rating_vs_complaints.png"); plt.close(fig)

    json.dump(M, open("outputs/metrics.json", "w"), indent=2)
    print(json.dumps(M, indent=2))
    print("\nWrote 4 figures and metrics.json")


if __name__ == "__main__":
    main()
