from pathlib import Path
import pandas as pd

RAW = Path("MDCR Summary AB 5.csv")
OUT = Path("cms_charges_clean.csv")

STATE_MAP = {
 "Alabama":"AL","Alaska":"AK","Arizona":"AZ","Arkansas":"AR","California":"CA",
 "Colorado":"CO","Connecticut":"CT","Delaware":"DE","District of Columbia":"DC",
 "Florida":"FL","Georgia":"GA","Hawaii":"HI","Idaho":"ID","Illinois":"IL",
 "Indiana":"IN","Iowa":"IA","Kansas":"KS","Kentucky":"KY","Louisiana":"LA",
 "Maine":"ME","Maryland":"MD","Massachusetts":"MA","Michigan":"MI","Minnesota":"MN",
 "Mississippi":"MS","Missouri":"MO","Montana":"MT","Nebraska":"NE","Nevada":"NV",
 "New Hampshire":"NH","New Jersey":"NJ","New Mexico":"NM","New York":"NY",
 "North Carolina":"NC","North Dakota":"ND","Ohio":"OH","Oklahoma":"OK","Oregon":"OR",
 "Pennsylvania":"PA","Rhode Island":"RI","South Carolina":"SC","South Dakota":"SD",
 "Tennessee":"TN","Texas":"TX","Utah":"UT","Vermont":"VT","Virginia":"VA",
 "Washington":"WA","West Virginia":"WV","Wisconsin":"WI","Wyoming":"WY","Puerto Rico":"PR"
}

def fuse_two_row_header(path: Path) -> pd.DataFrame:
    raw = pd.read_csv(path, header=None, dtype=str, engine="python", skip_blank_lines=False)
    header_idx = None
    for i in range(min(60, len(raw))):
        if any("Area of Residence" in str(v) for v in raw.iloc[i].astype(str).tolist()):
            header_idx = i
            break
    if header_idx is None:
        raise RuntimeError("Couldn't find header row with 'Area of Residence'.")

    top = raw.iloc[header_idx].astype(str).fillna("").str.strip().tolist()
    nxt = raw.iloc[header_idx+1].astype(str).fillna("").str.strip().tolist()
    L = max(len(top), len(nxt))
    top += [""]*(L-len(top)); nxt += [""]*(L-len(nxt))
    fused = []
    for a,b in zip(top,nxt):
        a = "" if a.startswith("Unnamed") else a
        b = "" if b.startswith("Unnamed") else b
        name = (a + " " + b).strip() if (a or b) else "Unnamed"
        fused.append(name)
    body = raw.iloc[header_idx+2:].reset_index(drop=True)
    body.columns = fused
    keep = [c for c in body.columns if not (c.startswith("Unnamed") and body[c].isna().all())]
    return body[keep]

def find_col(df: pd.DataFrame, phrases):
    for col in df.columns:
        low = col.lower()
        if all(p.lower() in low for p in phrases):
            return col
    return None

def main():
    df = fuse_two_row_header(RAW)

    col_area = find_col(df, ["area of residence"])
    col_util = find_col(df, ["program payments","per person","utilization"])
    col_enrl = find_col(df, ["total","original","part a","part b","enrollee"])

    if not col_area or not col_util:
        raise RuntimeError("Couldn't find needed CMS columns.\n"
                           f"Found cols: {df.columns.tolist()[:60]}")

    keep = [col_area, col_util] + ([col_enrl] if col_enrl else [])
    out = df[keep].copy()
    out.columns = ["state_name","allowed_charges_per_person"] + (["beneficiaries"] if col_enrl else [])

    out["state_name"] = out["state_name"].astype(str).str.strip()
    out["allowed_charges_per_person"] = (out["allowed_charges_per_person"].astype(str)
                                         .str.replace(r"[\$,]", "", regex=True).str.strip())
    if "beneficiaries" in out.columns:
        out["beneficiaries"] = (out["beneficiaries"].astype(str)
                                .str.replace(",", "", regex=False).str.strip())

    bad = {"All Areas","United States","Total","—","–",""}
    out = out[~out["state_name"].isin(bad)].copy()
    out["state_code"] = out["state_name"].map(STATE_MAP)

    cols = ["state_name","state_code","beneficiaries","allowed_charges_per_person"]
    cols = [c for c in cols if c in out.columns]
    out = out[cols].reset_index(drop=True)

    out.to_csv(OUT, index=False)
    print("Wrote", OUT.resolve())
    print(out.head(8).to_string(index=False))

if __name__ == "__main__":
    main()
