# scripts/analyze.py  -- usage: python scripts/analyze.py results/main prompts/main.csv
import subprocess, sys
out, prompts = sys.argv[1], sys.argv[2]
for cmd in ([sys.executable, "-m", "attest_harness.check_requests", f"{out}/requests", prompts],
            [sys.executable, "-m", "attest_harness.report_tables", f"{out}/results.csv"],
            [sys.executable, "-m", "attest_harness.plot", f"{out}/results.csv", f"{out}/figure1.png"]):
    print("$", " ".join(cmd)); subprocess.run(cmd, check=True)
