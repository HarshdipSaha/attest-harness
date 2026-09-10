from __future__ import annotations
import math
import pandas as pd
from statsmodels.stats.contingency_tables import mcnemar

def wilson_ci(k: int, n: int, z: float = 1.96) -> tuple[float, float]:
    if n == 0: return (0.0, 0.0)
    p = k / n; d = 1 + z * z / n
    c = (p + z * z / (2 * n)) / d
    h = z * math.sqrt(p * (1 - p) / n + z * z / (4 * n * n)) / d
    return (max(0.0, c - h), min(1.0, c + h))

def refusal_table(df: pd.DataFrame, label_col: str = "judge_label", positive=("refuse",)) -> pd.DataFrame:
    d = df.assign(r=df[label_col].isin(positive).astype(int))
    g = d.groupby(["model", "arm"])["r"].agg(["sum", "count"])
    g["rate"] = g["sum"] / g["count"]
    g[["ci_lo", "ci_hi"]] = g.apply(lambda r: pd.Series(wilson_ci(int(r["sum"]), int(r["count"]))), axis=1)
    return g

def mcnemar_pairs(df: pd.DataFrame, arm_a: str, arm_b: str, label_col="judge_label", positive=("refuse",)) -> pd.DataFrame:
    out = {}
    for model, sub in df.groupby("model"):
        a = sub[sub.arm == arm_a].set_index("prompt_id")[label_col].isin(positive)
        b = sub[sub.arm == arm_b].set_index("prompt_id")[label_col].isin(positive)
        idx = a.index.intersection(b.index); a, b = a[idx], b[idx]
        n01 = int(((~a) & b).sum()); n10 = int((a & (~b)).sum())
        table = [[int((a & b).sum()), n10], [n01, int(((~a) & (~b)).sum())]]
        res = mcnemar(table, exact=True)
        out[model] = dict(n=len(idx), refuse_a=int(a.sum()), refuse_b=int(b.sum()),
                          diff_pp=100 * (b.mean() - a.mean()), discordant=n01 + n10, p_value=float(res.pvalue))
    return pd.DataFrame(out).T
