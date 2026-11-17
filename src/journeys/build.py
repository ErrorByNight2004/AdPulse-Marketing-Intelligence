# src/journeys/build.py
import os
import ast
import numpy as np
import pandas as pd

# ---------- helpers ----------
SEQ_COLS = ["campaign_seq", "click_seq", "cost_seq", "time_since_last_click_seq"]

def _to_pylist(x):
    if isinstance(x, list): return x
    if isinstance(x, (np.ndarray, pd.Series)): return x.tolist()
    if isinstance(x, str) and x.strip().startswith('[') and x.strip().endswith(']'):
        try: return ast.literal_eval(x)
        except Exception: return []
    if x is None or (isinstance(x, float) and pd.isna(x)) or x == "": return []
    return [x]

def _make_row(uid, sub: pd.DataFrame, converted: bool, conv_id: int = -1, conv_time: int = -1):
    # sub is a slice of impressions in order
    return dict(
        uid=uid,
        conversion=int(converted),
        conversion_id=int(conv_id),
        conv_time=int(conv_time),
        length=int(len(sub)),
        campaign_seq=sub["campaign"].astype(str).tolist(),
        click_seq=sub["click"].astype(int).tolist(),
        cost_seq=sub["cost"].astype(float).tolist(),
        time_since_last_click_seq=sub["time_since_last_click"].astype(float).tolist(),
        # optional: keep first/last campaign ids as convenience
        first_campaign_id=str(sub["campaign"].iloc[0]) if len(sub) > 0 else "-1",
        last_campaign_id=str(sub["campaign"].iloc[-1]) if len(sub) > 0 else "-1",
        # optional aggregates you may want directly ready (can be recomputed later too)
        total_cost=float(sub["cost"].sum()),
        num_clicks=int(sub["click"].sum())
    )

# ---------- core builder ----------
def build_journeys_from_impressions(df: pd.DataFrame) -> pd.DataFrame:
    """
    Input df = raw impressions with columns:
      timestamp, uid, campaign, conversion, conversion_timestamp, conversion_id,
      attribution, click, click_pos, click_nb, cost, cpo, time_since_last_click, cat1..cat9

    Output journeys table with one row per *journey segment*:
      - one row for EACH conversion segment (converted=1)
      - a final 'tail' segment after the last conversion (converted=0) if impressions remain
      - if a user never converts, a single non-conversion segment over all impressions
    """
    required = ["timestamp", "uid", "campaign", "conversion_id",
                "conversion_timestamp", "click", "cost", "time_since_last_click"]
    missing = [c for c in required if c not in df.columns]
    if missing:
        raise ValueError(f"Missing required columns in impressions: {missing}")

    # ensure sort by user-time
    df = df.sort_values(["uid", "timestamp"], kind="mergesort").reset_index(drop=True)

    rows = []
    # observed=True avoids category expansion warning in future pandas
    for uid, user in df.groupby("uid", sort=False, observed=True):
        # strictly ensure within-user time order
        user = user.sort_values("timestamp", kind="mergesort")

        # indices where a conversion is observed (conversion_id != -1)
        has_conv = (user["conversion_id"] != -1)
        conv_indices = user.index[has_conv].tolist()

        # cursor points to the start of the current segment
        uidx = user.index.tolist()
        if not uidx:
            continue
        cursor_pos = 0  # position in uidx list

        def segment_from_cursor_to(target_idx_in_user_inclusive: int) -> pd.DataFrame:
            """slice sub-dataframe from current cursor to target index (inclusive)"""
            nonlocal cursor_pos
            start_idx = uidx[cursor_pos]
            end_idx = target_idx_in_user_inclusive
            return user.loc[start_idx:end_idx]

        def advance_cursor_past(target_idx_in_user_inclusive: int):
            """move cursor to the next position after target"""
            nonlocal cursor_pos
            next_pos = user.index.get_loc(target_idx_in_user_inclusive) + 1
            cursor_pos = next_pos

        # walk each conversion to create a converted journey segment
        for ci in conv_indices:
            sub = segment_from_cursor_to(ci)
            conv_row = user.loc[ci]
            if len(sub) > 0:
                rows.append(_make_row(
                    uid=uid,
                    sub=sub,
                    converted=True,
                    conv_id=int(conv_row["conversion_id"]),
                    conv_time=int(conv_row["conversion_timestamp"])
                ))
            advance_cursor_past(ci)
            if cursor_pos >= len(uidx):
                break

        # tail after last conversion (if any impressions remain)
        if cursor_pos < len(uidx):
            tail = user.loc[uidx[cursor_pos]:uidx[-1]]
            if len(tail) > 0:
                rows.append(_make_row(
                    uid=uid,
                    sub=tail,
                    converted=False
                ))

        # Users with no conversions would skip the loop above and get only the tail as non-conversion.
        # Users with conversions will have N converted segments + 1 non-converted tail (if leftover impressions exist).

    J = pd.DataFrame(rows)

    # idempotency: ensure list-typed cols are lists (if serialized/loaded elsewhere)
    for c in SEQ_COLS:
        if c in J.columns:
            J[c] = J[c].apply(_to_pylist)

    # light sanity columns (optional)
    if "first_campaign_id" not in J.columns:
        J["first_campaign_id"] = J["campaign_seq"].apply(lambda s: str(s[0]) if len(s) > 0 else "-1")
    if "last_campaign_id" not in J.columns:
        J["last_campaign_id"] = J["campaign_seq"].apply(lambda s: str(s[-1]) if len(s) > 0 else "-1")

    return J

# ---------- IO wrappers ----------
def build_and_save(impressions: pd.DataFrame,
                   out_all="../data/processed/journeys_all.parquet",
                   out_conv="../data/processed/journeys_converted.parquet"):
    J = build_journeys_from_impressions(impressions)
    # save both views
    os.makedirs(os.path.dirname(out_all), exist_ok=True)
    J.to_parquet(out_all, index=False)

    J_conv = J[J["conversion"] == 1].copy()
    J_conv.to_parquet(out_conv, index=False)

    return J, J_conv

def load_impressions_from_tsv(tsv_path: str, dtypes=None, nrows=None):
    return pd.read_csv(tsv_path, sep="\t", dtype=dtypes, nrows=nrows)

def load_impressions_from_parquet(parquet_path: str):
    return pd.read_parquet(parquet_path)
