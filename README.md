<div align="center">

# 🛡️ attest-harness

### Authorization is a **channel**, not a word.

[![License: MIT](https://img.shields.io/badge/License-MIT-A371F7.svg?style=flat-square)](LICENSE)
[![Python](https://img.shields.io/badge/Python-3.12+-3776AB?style=flat-square&logo=python&logoColor=white)](pyproject.toml)
[![Crypto](https://img.shields.io/badge/Ed25519-signed%20attestation-3fb950?style=flat-square)](ir_attest/TOKEN_SPEC.md)
[![Tests](https://img.shields.io/badge/tests-45%20offline-3fb950?style=flat-square)](tests/)
[![Pre-registered](https://img.shields.io/badge/hypotheses-pre--registered-8c78f5?style=flat-square)](docs/PREREG.md)
[![Sprint](https://img.shields.io/badge/Apart%20Research-AI%20Incident%20Response%20Sprint-0d1117?style=flat-square)](docs/ABOUT-HACKATHON.md)

**[How it works](#how-it-works)** · **[The result](#the-result)** · **[Try it](#try-it)**

</div>

<div align="center">
  <img src="docs/assets/demo.gif" alt="The same incident-response request with the authorization signal in three different places: typed in user text (17% refused), in a verified channel (0% refused), and a typed claim contradicted by the verifier (100% refused)." width="880">
</div>

---

## Two incidents, one bug

**July 2026.** Hugging Face's own responders — genuinely authorized, working their own breach — asked frontier models to help reconstruct the intrusion. They were **refused**, and fell back to a weaker self-hosted model mid-incident.

**The same summer.** Aurora ransomware operators told Cursor's coding agent their attack was *"an authorized penetration test."* It **helped them** hands-on exploit more than ten real companies.

Same word. *Authorized.* The real defender was turned away; the real attacker was let in.

The reason is that guardrails read authorization out of the **text of the request** — and text is precisely the thing an attacker forges for free and a defender phrases badly. The published measurement makes it worse than neutral: adding an explicit authorization claim **raised** refusal from 11.6% to 21.8%. Saying you are authorized makes you look *more* suspicious, not less.

So stop putting authorization in the sentence.

## How it works

Two small pieces. The first makes authorization into something you can *check*; the second measures whether models actually respond to it.

**1. A real verifier — `ir_attest`.** Your security team signs a short-lived, scoped attestation for a named responder and a named incident. Ed25519, 15 minutes by default, scoped to `ir:forensics`. The verifier checks signature, expiry, scope and replay, and returns a structured VALID / INVALID — never a vibe.

**2. A paired replay — `attest_harness`.** The *same* forensic prompt goes to three hosted models under six arms that differ in exactly one thing: **where the authorization signal sits.**

| Arm | Where the signal sits | What it really is |
|---|---|---|
| `A1` baseline | nowhere | the control |
| `A2` prose claim | typed in the user's message | anyone can type this |
| `A3` in-band token | token pasted into the user's message | still just text |
| `A4a` verified system | verifier result in the **system** turn | signed and checked |
| `A4b` verified tool | the model **calls** the verifier as a tool | signed and checked |
| `A5` conflict | user claims authorized, **verifier says INVALID** | the discrimination test |

Arm 5 is the one that matters most. A channel that merely lowers refusals is a jailbreak. A channel worth deploying has to honour VALID **and reject INVALID even when the user text insists otherwise** — so that's measured, and reported either way.

Hypotheses, arms, sample size and the judging rubric were [committed before the run](docs/PREREG.md), so no arm was picked after seeing results.

## The result

<div align="center">
  <img src="docs/assets/results.png" alt="Refusal rate by arm and model. Verified system and verified tool channels sit at 0% for all three models, while the conflict arm reaches 100%, 37% and 30%." width="880">
</div>

Read it in one line: **a signed credential in a channel the model can check produces zero refusals — and a typed claim that contradicts that channel produces total refusal.**

- **Verified channels are clean.** `A4a` and `A4b` are at **0%** refusal on all three models. A genuinely authorized responder gets their forensic work done.
- **Typing it does nothing — or backfires.** The prose claim pushed gpt-oss-120b to **17%** refusal, replicating the anti-signal effect. Pasting the token into user text moved nothing: it's the *channel* that carries meaning, not the keyword.
- **The channel discriminates.** When the user claims authorization and the verifier returns INVALID, refusal jumps to **100% / 37% / 30%** — the largest effect in the experiment and statistically significant on all three models. This is the evidence that it isn't a bypass.

Every number above comes from the committed pilot run — 30 prompts × 6 arms × 3 models = **540 model calls**, judged per response, with paired McNemar tests and Wilson intervals in [`results/smoke/tables.txt`](results/smoke/tables.txt). The full 220-prompt set ships in [`prompts/main.csv`](prompts/main.csv).

## Try it

Issue and verify a real attestation — no API key, no network:

```bash
pip install -e .[dev]

python -m ir_attest issue --iss "Hugging Face" --sub alice \
    --scope ir:forensics --incident IR-2026-07 --ttl 900
python -m ir_attest verify <token> --scope ir:forensics   # exits 1 if INVALID
```

Run the full suite — it uses fakes instead of SDK clients, so it costs nothing and runs offline:

```bash
pytest
```

Replay the experiment against the models yourself:

```bash
python -m attest_harness.runner --n 220 --out results/main --cap 60
```

The harness enforces a hard dollar cap before every paid call, caches every completion so a crash resumes for free, and audits the raw request bodies to prove no authorization text leaked into a supposedly clean arm.

## Built with

**Ed25519** via `cryptography` · **OpenAI + Anthropic SDK adapters** (any OpenAI-compatible endpoint works) · **pandas / scipy / statsmodels** for Wilson intervals and exact McNemar tests · **matplotlib** for the figure. Built for the Apart Research × CeSIA **AI Incident Response Sprint**, Open Track.

Deeper reading: [the spec](docs/SPEC.md) · [pre-registration](docs/PREREG.md) · [token spec](ir_attest/TOKEN_SPEC.md) · [status & decision log](docs/STATUS.md) · [deviations](docs/DEVIATIONS.md)

<div align="center">
<br>
<b>attest-harness</b> — a credential your security team signs, not a sentence anyone can type.
</div>
