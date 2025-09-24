from pathlib import Path
import pandas as pd

def clean_cms(path: Path) -> pd.DataFrame:

    raw = pd.read_csv(path, header=None, dtype=str, engine="python", skip_blank_lines=False)
    header_idx = None
    for i in range(min(50, len(raw))):
        row_vals = raw.iloc[i].astype(str).tolist()
        if any("Area of Residence" in str(v) for v in row_vals):
            header_idx = i
            break
    if header_idx is None:
        raise KeyError("Csnt locate header row containing 'Area of Residence'.")

    top = raw.iloc[header_idx].astype(str).fillna("").str.strip().tolist()
    nxt = raw.iloc[header_idx + 1].astype(str).fillna("").str.strip().tolist() if header_idx + 1 < len(raw) else []
    maxlen = max(len(top), len(nxt))
    top += [""] * (maxlen - len(top))
    nxt += [""] * (maxlen - len(nxt))
    fused = []
    for a, b in zip(top, nxt):
        name = (a if a and a != "Unnamed" else "")
        if b and b != "Unnamed":
            name = (name + " " + b).strip() if name else b
        fused.append(name if name else "Unnamed")

    body = raw.iloc[header_idx + 2:].reset_index(drop=True)
    body.columns = fused

    keep_cols = [c for c in body.columns if not (c.startswith("Unnamed") and body[c].isna().all())]
    df = body[keep_cols].copy()
    df.columns = [c.strip() for c in df.columns]

    def find_col(phrases):
        for col in df.columns:
            low = col.lower()
            if all(p.lower() in low for p in phrases):
                return col
        return None

    col_area = find_col(["area of residence"])
    col_pay_per_util = find_col(["program payments", "per person", "utilization"])
    col_enrollees = find_col(["total", "original", "part a", "part b", "enrollee"])

    if not col_area or not col_pay_per_util:
        raise KeyError("Couldn't find CMS columns after fusing header. Columns seen: " + " | ".join(df.columns[:30]))

    keep = [col_area, col_pay_per_util] + ([col_enrollees] if col_enrollees else [])
    cms = df[keep].copy()
    cms.columns = ["state_name", "allowed_charges_per_person"] + (["beneficiaries"] if col_enrollees else [])

    def clean_money(x):
        if pd.isna(x): return None
        return str(x).replace("$","").replace(",","").strip()

    def clean_int(x):
        if pd.isna(x): return None
        return str(x).replace(",","").strip()

    cms["state_name"] = cms["state_name"].astype(str).str.strip()
    cms["state_code"] = cms["state_name"].map(STATE_MAP)

    if "allowed_charges_per_person" in cms.columns:
        cms["allowed_charges_per_person"] = cms["allowed_charges_per_person"].map(clean_money)
    if "beneficiaries" in cms.columns:
        cms["beneficiaries"] = cms["beneficiaries"].map(clean_int)

    bad = {"All Areas","United States","Total","—","–",""}
    cms = cms[~cms["state_name"].isin(bad)].copy()

    out_cols = ["state_name","state_code","beneficiaries","allowed_charges_per_person"]
    out_cols = [c for c in out_cols if c in cms.columns]
    cms = cms[out_cols].reset_index(drop=True)

    print(f"[CMS] rows: {len(cms)}  columns: {cms.columns.tolist()}")
    return cms
