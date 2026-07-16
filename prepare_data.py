"""
prepare_data.py — clean the three raw sources into tidy files in data/real/.

Raw inputs (place in data/raw/):
  reviews_raw.csv           app-store reviews for UK telecom/utility brands, with an AI-mention flag
  citizens_advice_raw.csv   Citizens Advice energy supplier service ratings, quarterly
  ofcom_q4_2025_raw.csv      Ofcom Telecoms and Pay TV complaints summary (messy multi-table export)

Writes:
  data/real/reviews_clean.csv
  data/real/ca_panel.csv
  data/real/ofcom_complaints.csv
"""
import os, re, glob
import numpy as np
import pandas as pd

HERE = os.path.dirname(os.path.abspath(__file__))
RAW = os.path.join(HERE, "data", "raw")
REAL = os.path.join(HERE, "data", "real")
os.makedirs(REAL, exist_ok=True)


def find(sub):
    hits = glob.glob(os.path.join(RAW, "**", "*" + sub + "*"), recursive=True)
    if not hits:
        raise FileNotFoundError(sub + " not found under data/raw")
    return sorted(hits, key=len)[0]


def clean_reviews():
    r = pd.read_csv(find("reviews_raw"))
    r["date"] = pd.to_datetime(r["date"], errors="coerce", utc=True)
    r["year"] = r["date"].dt.year
    r["ai_related"] = r["ai_related"].astype(str).str.lower().isin(["true", "1", "yes"])
    r = r.dropna(subset=["score", "brand"])
    r["score"] = pd.to_numeric(r["score"], errors="coerce")
    r = r.dropna(subset=["score"])
    return r[["brand", "platform", "date", "year", "score", "content", "ai_related", "matched_terms"]]


def clean_ca():
    c = pd.read_csv(find("citizens_advice_raw")).rename(columns={
        "Supplier": "supplier", "Quarter": "quarter", "Overall_Star_Rating": "star_rating",
        "Call_Wait_Time_Seconds": "call_wait_s", "Email_Response_Under_2_Days_Pct": "email_resp_pct",
        "Complaints_per_10k_Customers": "complaints_per_10k"})
    qp = c["quarter"].str.extract(r"Q(\d)\s+(\d{4})")
    c["q"] = pd.to_numeric(qp[0], errors="coerce")
    c["year"] = pd.to_numeric(qp[1], errors="coerce")
    c = c.dropna(subset=["q", "year"])
    c["q"] = c["q"].astype(int); c["year"] = c["year"].astype(int)
    c["t"] = c["year"] * 4 + (c["q"] - 1)   # ordinal quarter index
    return c


def _svc_name(section):
    s = section.lower()
    if "relative volume" in s: return None
    if "fixed broadband" in s: return "Fixed broadband"
    if "landline" in s: return "Landline"
    if "pay monthly" in s or "pay-monthly" in s: return "Pay-monthly mobile"
    if "pay tv" in s: return "Pay TV"
    return None


def clean_ofcom():
    raw = pd.read_csv(find("ofcom_q4_2025_raw"), header=None, dtype=str)

    def is_quarter_row(i):
        v = raw.iat[i, 1] if raw.shape[1] > 1 else None
        return isinstance(v, str) and re.match(r"\d{4}\s+Q\d", v.strip()) is not None

    qrow = next(i for i in range(len(raw)) if is_quarter_row(i))
    quarters = [str(x).strip() if pd.notna(x) else None for x in raw.iloc[qrow, 1:].tolist()]

    records, section = [], None
    for i in range(len(raw)):
        lab = raw.iat[i, 0]
        if not isinstance(lab, str) or lab.strip() == "":
            continue
        lab = lab.strip()
        if "per 100,000" in lab.lower():
            section = lab; continue
        if lab.lower().startswith("note"):
            section = None; continue
        if is_quarter_row(i):
            continue
        if section:
            svc = _svc_name(section)
            if svc is None:
                continue
            vals = raw.iloc[i, 1:1 + len(quarters)].tolist()
            for q, v in zip(quarters, vals):
                if q and pd.notna(v) and str(v).strip() != "":
                    try:
                        records.append(dict(service=svc, provider=lab,
                                            quarter=q, complaints_per_100k=float(str(v).replace(",", ""))))
                    except ValueError:
                        pass
    df = pd.DataFrame(records)
    qp = df["quarter"].str.extract(r"(\d{4})\s+Q(\d)")
    df["year"] = qp[0].astype(int); df["q"] = qp[1].astype(int)
    df["t"] = df["year"] * 4 + (df["q"] - 1)
    df["is_industry_avg"] = df["provider"].str.lower().str.contains("industry average")
    return df


if __name__ == "__main__":
    rv = clean_reviews(); rv.to_csv(os.path.join(REAL, "reviews_clean.csv"), index=False)
    ca = clean_ca(); ca.to_csv(os.path.join(REAL, "ca_panel.csv"), index=False)
    of = clean_ofcom(); of.to_csv(os.path.join(REAL, "ofcom_complaints.csv"), index=False)
    print(f"reviews_clean.csv: {rv.shape}  (ai-related {rv.ai_related.mean():.1%})")
    print(f"ca_panel.csv:      {ca.shape}  suppliers={ca.supplier.nunique()} quarters={ca.quarter.nunique()}")
    print(f"ofcom_complaints.csv: {of.shape}  services={sorted(of.service.unique())}")
    print(f"  ofcom providers: {of.provider.nunique()}  quarters {of.year.min()}Q{of[of.year==of.year.min()].q.min()} .. {of.year.max()}Q{of[of.year==of.year.max()].q.max()}")
