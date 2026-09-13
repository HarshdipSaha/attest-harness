"""Render docs/assets/results.png — a dark benchmark card for the README.

Reads results/smoke/summary.csv (the committed pilot run) and draws refusal
rate per arm per model. Pure Pillow, no external tooling.

    py scripts/make_results_chart.py
"""
from __future__ import annotations

import csv
from pathlib import Path

from PIL import Image, ImageDraw

from make_demo_gif import (AMBER, BG, BORDER, CHIP_BG, FAINT, GREEN, INDIGO,
                           MUTED, PANEL, R, RED, S, TXT, font, rr, tl, tx)

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "docs" / "assets"
SUMMARY = ROOT / "results" / "smoke" / "summary.csv"

CYAN = (79, 209, 197)

W, H = 920, 544

f_kick = font("seguisb.ttf", 12)
f_title = font("segoeuib.ttf", 25)
f_sub = font("segoeui.ttf", 13)
f_arm = font("seguisb.ttf", 14)
f_tag = font("segoeui.ttf", 11)
f_val = font("seguisb.ttf", 12)
f_leg = font("seguisb.ttf", 12)

ARMS = [
    ("A1_baseline", "no claim at all", "control", MUTED),
    ("A2_prose_claim", "claim typed in user text", "anyone can type this", AMBER),
    ("A3_inband_token", "token pasted in user text", "still just text", AMBER),
    ("A4a_verified_system", "verified · system channel", "signed, checked", GREEN),
    ("A4b_verified_tool", "verified · real tool call", "signed, checked", GREEN),
    ("A5_conflict", "claim vs verifier", "the discrimination test", RED),
]
MODELS = [("gpt_oss_120b", "gpt-oss-120b", INDIGO),
          ("gpt_oss_20b", "gpt-oss-20b", CYAN),
          ("qwen3_8_27b", "qwen3.8-27b", AMBER)]


def main():
    rates = {}
    with open(SUMMARY, newline="") as fh:
        for row in csv.DictReader(fh):
            rates[(row["model"], row["arm"])] = float(row["rate"])

    img = Image.new("RGB", (W * S, H * S), BG)
    d = ImageDraw.Draw(img)

    tx(d, (40, 30), "RESULT", f_kick, INDIGO)
    tx(d, (40, 48), "Move the authorization. Watch the refusals move.", f_title, TXT)
    tx(d, (40, 84),
       "identical incident-response prompts · 540 model calls · refusal judged per response",
       f_sub, MUTED)

    # legend
    lx = 40
    for _, label, color in MODELS:
        d.ellipse(R(lx, 112, lx + 9, 121), fill=color)
        tx(d, (lx + 15, 110), label, f_leg, MUTED)
        lx += tl(d, label, f_leg) + 42

    x0, track = 300, 560
    y = 146
    for key, label, tag, lcolor in ARMS:
        rr(d, (36, y - 8, W - 36, y + 52), 10, fill=PANEL)
        tx(d, (54, y + 2), label, f_arm, TXT)
        tx(d, (54, y + 22), tag, f_tag, lcolor)

        by = y + 2
        for mkey, _, color in MODELS:
            pct = rates.get((mkey, key), 0.0)
            rr(d, (x0, by, x0 + track, by + 12), 6, fill=CHIP_BG)
            fillw = max(4, track * pct)
            rr(d, (x0, by, x0 + fillw, by + 12), 6, fill=color)
            tx(d, (x0 + track + 12, by - 1), f"{pct*100:.0f}%", f_val,
               color if pct > 0 else FAINT)
            by += 15
        y += 60

    tx(d, (40, H - 30),
       "0% refusals through a verified channel. 100% when the typed claim contradicts it.",
       f_sub, TXT)

    img.resize((W, H), Image.LANCZOS).save(OUT / "results.png")
    print("wrote", OUT / "results.png")


if __name__ == "__main__":
    main()
