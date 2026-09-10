import sys, pandas as pd
from .stats import refusal_table, mcnemar_pairs
df = pd.read_csv(sys.argv[1])
for col in ("judge_label", "regex_label"):
    print(f"\n== {col} ==\n", refusal_table(df, col).round(3))
    for a, b, h in (("A2_prose_claim", "A4a_verified_system", "H1"), ("A1_baseline", "A5_conflict", "H2"),
                    ("A1_baseline", "A2_prose_claim", "H3"), ("A2_prose_claim", "A4b_verified_tool", "H1-tool"),
                    ("A2_prose_claim", "A3_inband_token", "keyword-vs-structure")):
        print(f"\n{h}: {a} -> {b}\n", mcnemar_pairs(df, a, b, col).round(4))
import os
refusal_table(df).reset_index().to_csv(os.path.join(os.path.dirname(sys.argv[1]), "summary.csv"), index=False)
