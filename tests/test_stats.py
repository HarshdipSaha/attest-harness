import pandas as pd
from attest_harness.stats import wilson_ci, refusal_table, mcnemar_pairs

def test_wilson_ci_basic():
    lo, hi = wilson_ci(20, 100)
    assert 0.12 < lo < 0.2 < hi < 0.29

def _df():
    rows = []
    for i in range(40):
        rows.append(dict(model="m", arm="A2_prose_claim", prompt_id=f"p{i}", judge_label="refuse" if i < 20 else "comply"))
        rows.append(dict(model="m", arm="A4a_verified_system", prompt_id=f"p{i}", judge_label="refuse" if i < 5 else "comply"))
    return pd.DataFrame(rows)

def test_refusal_table_and_mcnemar():
    t = refusal_table(_df(), label_col="judge_label")
    assert abs(t.loc[("m", "A2_prose_claim"), "rate"] - 0.5) < 1e-9
    res = mcnemar_pairs(_df(), "A2_prose_claim", "A4a_verified_system", label_col="judge_label")
    assert res.loc["m", "p_value"] < 0.01 and res.loc["m", "diff_pp"] < 0
