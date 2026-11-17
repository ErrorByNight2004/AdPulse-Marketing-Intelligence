# src/pipeline/analyze_attribution_xgb.py
import os, json, ast, argparse
import numpy as np
import pandas as pd
from sklearn.model_selection import train_test_split
from sklearn.metrics import roc_auc_score, log_loss
import xgboost as xgb
import shap

# -------------------- helpers --------------------
def ensure_dir(p): os.makedirs(p, exist_ok=True)

def to_pylist(x):
    if isinstance(x, list): return x
    if isinstance(x, (np.ndarray, pd.Series)): return x.tolist()
    if isinstance(x, str) and x.strip().startswith('[') and x.strip().endswith(']'):
        try: return ast.literal_eval(x)
        except Exception: return []
    if x is None or (isinstance(x, float) and pd.isna(x)) or x == "": return []
    return [x]

def safe_mean_pos(vals):
    arr = np.array([v for v in vals if (isinstance(v,(int,float)) and v>=0)], dtype=float)
    return float(arr.mean()) if arr.size else 0.0

# -------------------- load --------------------
def load_journeys(path_parquet: str) -> pd.DataFrame:
    J = pd.read_parquet(path_parquet)
    for c in ["campaign_seq","click_seq","cost_seq","time_since_last_click_seq"]:
        if c in J.columns:
            J[c] = J[c].apply(to_pylist)
    return J

# -------------------- feature engineering --------------------
def build_features(J: pd.DataFrame, label_prefers_attribution=True) -> pd.DataFrame:
    F = pd.DataFrame()
    F["uid"] = J["uid"]

    # label: prefer 'attribution' if present, else 'conversion'
    label_col = "attribution" if (label_prefers_attribution and "attribution" in J.columns) else "conversion"
    F["conversion"] = J[label_col].astype(int)

    # path stats
    F["path_length"] = J["campaign_seq"].apply(len).clip(upper=20)
    F["num_clicks"]  = J["click_seq"].apply(lambda x: int(np.sum(x))).clip(upper=20)
    F["unique_campaigns"] = J["campaign_seq"].apply(lambda x: len(set(x)))

    # costs (log1p)
    F["total_cost"] = J["cost_seq"].apply(np.sum)
    F["avg_cost"]   = J["cost_seq"].apply(lambda x: float(np.mean(x)) if len(x)>0 else 0.0)
    F["total_cost"] = np.log1p(F["total_cost"])
    F["avg_cost"]   = np.log1p(F["avg_cost"])

    # time gaps (seconds, -1 means none) → mean of non-negative, then log1p
    F["avg_time_gap"] = J["time_since_last_click_seq"].apply(safe_mean_pos)
    F["avg_time_gap"] = np.log1p(F["avg_time_gap"])

    # first / last campaign (codes for model; keep raw ids for SHAP mapping)
    first_id = J["campaign_seq"].apply(lambda s: str(s[0]) if len(s)>0 else "-1")
    last_id  = J["campaign_seq"].apply(lambda s: str(s[-1]) if len(s)>0 else "-1")
    F["first_campaign"] = pd.Categorical(first_id).codes
    F["last_campaign"]  = pd.Categorical(last_id).codes
    F["_first_campaign_id"] = first_id
    F["_last_campaign_id"]  = last_id
    return F

# -------------------- train XGBoost (native) --------------------
def train_xgb_native(X_train, y_train, X_val, y_val, X_test, y_test,
                     params=None, num_boost_round=2000, early_stopping_rounds=100):
    if params is None:
        params = dict(
            objective="binary:logistic",
            eval_metric=["logloss","auc"],
            eta=0.05,
            max_depth=6,
            subsample=0.8,
            colsample_bytree=0.8,
            seed=42
        )
    dtr = xgb.DMatrix(X_train, label=y_train)
    dva = xgb.DMatrix(X_val,   label=y_val)
    dte = xgb.DMatrix(X_test,  label=y_test)

    booster = xgb.train(
        params=params,
        dtrain=dtr,
        num_boost_round=num_boost_round,
        evals=[(dtr,"train"), (dva,"val")],
        early_stopping_rounds=early_stopping_rounds,
        verbose_eval=False
    )

    p_val  = booster.predict(dva, iteration_range=(0, booster.best_iteration+1))
    p_test = booster.predict(dte, iteration_range=(0, booster.best_iteration+1))

    metrics = dict(
        xgb_best_iter=int(booster.best_iteration),
        xgb_auc_val=float(roc_auc_score(y_val, p_val)),
        xgb_logloss_val=float(log_loss(y_val, p_val)),
        xgb_auc_test=float(roc_auc_score(y_test, p_test)),
        xgb_logloss_test=float(log_loss(y_test, p_test)),
    )
    return booster, metrics

# -------------------- SHAP: global + campaign aggregation --------------------
def shap_global_and_campaign(booster, X_test_no_meta: pd.DataFrame, X_test_with_meta: pd.DataFrame,
                             y_test: pd.Series, out_dir: str):
    explainer = shap.TreeExplainer(booster)
    shap_values = explainer.shap_values(X_test_no_meta)  # (n, d)

    # Global importance
    mean_abs = np.abs(shap_values).mean(axis=0)
    feat_importance = (pd.DataFrame({"feature": X_test_no_meta.columns, "mean_abs_shap": mean_abs})
                       .sort_values("mean_abs_shap", ascending=False))
    feat_importance.to_csv(os.path.join(out_dir, "shap_feature_importance.csv"), index=False)

    # Campaign-level via first/last features
    feat_idx = {f:i for i,f in enumerate(X_test_no_meta.columns)}
    if "first_campaign" not in feat_idx or "last_campaign" not in feat_idx:
        return {"warn": "first/last_campaign not found for SHAP aggregation"}

    i_first = feat_idx["first_campaign"]; i_last = feat_idx["last_campaign"]
    shap_first = shap_values[:, i_first]
    shap_last  = shap_values[:, i_last]

    # Raw campaign IDs aligned to X_test rows
    first_ids = X_test_with_meta["_first_campaign_id"].astype(str).values
    last_ids  = X_test_with_meta["_last_campaign_id"].astype(str).values
    mask_conv = (y_test.values == 1)

    def agg(ids, vals, mask, positive_only=False, name="credit"):
        v = np.where(vals>0, vals, 0.0) if positive_only else vals
        df = pd.DataFrame({"campaign_id": ids, name: v, "is_conv": mask})
        df = df[df["is_conv"]]
        return (df.groupby("campaign_id", as_index=False)[name]
                  .sum()
                  .sort_values(name, ascending=False))

    first_pos = agg(first_ids, shap_first, mask_conv, True,  "first_pos")
    last_pos  = agg(last_ids,  shap_last,  mask_conv, True,  "last_pos")
    first_raw = agg(first_ids, shap_first, mask_conv, False, "first_raw")
    last_raw  = agg(last_ids,  shap_last,  mask_conv, False, "last_raw")

    camp = (first_pos.merge(last_pos, on="campaign_id", how="outer")
                  .merge(first_raw, on="campaign_id", how="outer")
                  .merge(last_raw,  on="campaign_id", how="outer")).fillna(0.0)

    camp["credit_pos_total"] = camp["first_pos"] + camp["last_pos"]
    camp["credit_raw_total"] = camp["first_raw"] + camp["last_raw"]
    sum_pos = camp["credit_pos_total"].sum()
    sum_raw = camp["credit_raw_total"].sum()
    camp["share_pos"] = camp["credit_pos_total"] / sum_pos if sum_pos>0 else 0.0
    camp["share_raw"] = camp["credit_raw_total"] / sum_raw if sum_raw>0 else 0.0
    camp = camp.sort_values("credit_pos_total", ascending=False).reset_index(drop=True)

    camp.to_csv(os.path.join(out_dir, "model_based_attribution_shap.csv"), index=False)
    return {
        "shap_values_shape": list(shap_values.shape),
        "top_features": feat_importance.head(10).to_dict(orient="records")
    }

# -------------------- Rule-based attribution export --------------------
def rule_based_attribution(J: pd.DataFrame, out_path: str):
    rows = []
    for _, r in J.iterrows():
        conv = r.get("conversion", 0)
        if conv != 1:  # only attribute conversions
            continue
        seq = r["campaign_seq"]
        if not seq:
            continue
        conv_id = r.get("conversion_id", -1)

        # last-touch
        rows.append({"conversion_id": conv_id, "campaign": seq[-1], "credit": 1.0, "rule": "last_touch"})
        # first-touch
        rows.append({"conversion_id": conv_id, "campaign": seq[0], "credit": 1.0, "rule": "first_touch"})
        # linear
        c = 1.0 / len(seq)
        for camp in seq:
            rows.append({"conversion_id": conv_id, "campaign": camp, "credit": c, "rule": "linear"})
        # time-decay (decay=0.5)
        decay = 0.5
        weights = np.array([decay**(len(seq)-1-i) for i in range(len(seq))], dtype=float)
        weights /= weights.sum()
        for camp, w in zip(seq, weights):
            rows.append({"conversion_id": conv_id, "campaign": camp, "credit": float(w), "rule": "time_decay_d0.5"})

    df = pd.DataFrame(rows)
    agg = df.groupby(["campaign","rule"], as_index=False)["credit"].sum()
    agg.to_csv(out_path, index=False)
    print("Rule-based attribution saved ->", out_path)

# -------------------- main --------------------
def main(journeys_parquet, artifacts_dir="../artifacts", sample_frac=1.0, random_state=42):
    ensure_dir(artifacts_dir)
    bi_dir = os.path.join(artifacts_dir, "bi_exports"); ensure_dir(bi_dir)
    metrics_dir = os.path.join(artifacts_dir, "metrics"); ensure_dir(metrics_dir)

    # 1) Load journeys
    J = load_journeys(journeys_parquet)
    if 0 < sample_frac < 1.0:
        J = J.sample(frac=sample_frac, random_state=random_state).reset_index(drop=True)

    # 2) Features
    F = build_features(J, label_prefers_attribution=True)
    y = F["conversion"].astype(int)
    X = F.drop(columns=["uid","conversion"])

    # keep raw IDs for SHAP mapping; drop for model matrices
    keep_cols = ["_first_campaign_id","_last_campaign_id"]
    X_meta = X[keep_cols].copy()
    X_model = X.drop(columns=keep_cols)

    # 3) Split 70/15/15
    X_train, X_temp, y_train, y_temp = train_test_split(
        X_model.join(X_meta), y, test_size=0.30, random_state=random_state, stratify=y
    )
    X_val, X_test, y_val, y_test = train_test_split(
        X_temp, y_temp, test_size=0.50, random_state=random_state, stratify=y_temp
    )

    # 4) Train XGBoost
    booster, m_xgb = train_xgb_native(
        X_train.drop(columns=keep_cols), y_train,
        X_val.drop(columns=keep_cols),   y_val,
        X_test.drop(columns=keep_cols),  y_test
    )

    # 5) SHAP + campaign attribution (pass BOTH no_meta and with_meta)
    shap_info = shap_global_and_campaign(
        booster,
        X_test_no_meta = X_test.drop(columns=keep_cols),
        X_test_with_meta = X_test,
        y_test = y_test,
        out_dir = bi_dir
    )

    # 6) Rule-based exports
    rule_out = os.path.join(bi_dir, "campaign_attribution_rules.csv")
    rule_based_attribution(J, rule_out)

    # 7) Save metrics
    metrics = {**m_xgb, **({"shap": shap_info} if shap_info else {})}
    with open(os.path.join(metrics_dir, "model_based_attribution_metrics.json"), "w") as f:
        json.dump(metrics, f, indent=2)
    print("Saved metrics & exports in:", artifacts_dir)
    print(json.dumps(metrics, indent=2))

if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--journeys", type=str, default="../data/processed/journeys.parquet",
                    help="Path to journeys parquet")
    ap.add_argument("--artifacts", type=str, default="../artifacts", help="Artifacts dir")
    ap.add_argument("--sample-frac", type=float, default=1.0, help="Optional sample fraction (0-1)")
    args = ap.parse_args()
    main(args.journeys, args.artifacts, args.sample_frac)
