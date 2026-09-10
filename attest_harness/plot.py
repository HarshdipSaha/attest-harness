import sys
import pandas as pd
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from .stats import refusal_table

ARM_ORDER = ["A1_baseline", "A2_prose_claim", "A3_inband_token", "A4a_verified_system", "A4b_verified_tool", "A5_conflict"]
LABELS = ["baseline", "in-band prose claim", "in-band token", "verified (system)", "verified (tool)", "conflict"]

def plot(results_csv: str, out_png: str, label_col: str = "judge_label"):
    df = pd.read_csv(results_csv)
    t = refusal_table(df, label_col).reset_index()
    models = sorted(t.model.unique())
    fig, axes = plt.subplots(1, len(models), figsize=(4.2 * len(models), 3.6), sharey=True)
    axes = [axes] if len(models) == 1 else list(axes)
    for ax, m in zip(axes, models):
        s = t[t.model == m].set_index("arm").reindex(ARM_ORDER)
        err = [(s.rate - s.ci_lo).clip(lower=0), (s.ci_hi - s.rate).clip(lower=0)]  # clamp float noise at 0%/100%
        ax.bar(range(len(ARM_ORDER)), s.rate * 100, yerr=[e * 100 for e in err], capsize=3)
        ax.set_xticks(range(len(ARM_ORDER))); ax.set_xticklabels(LABELS, rotation=35, ha="right", fontsize=8)
        ax.set_title(m); ax.set_ylabel("refusal rate (%)")
    fig.suptitle("Refusal on identical IR prompts by authorization channel (Wilson 95% CI)")
    fig.tight_layout(); fig.savefig(out_png, dpi=160)

if __name__ == "__main__":
    plot(sys.argv[1], sys.argv[2])
