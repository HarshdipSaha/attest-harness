# Demo Script — "Authorization Is a Channel Property"

For the optional 3–5 minute video demo (Guidelines tab, optional but recommended). Written as a
narration + on-screen-action script. Bracketed `[LIKE THIS]` items are placeholders to fill in
once `results/main` exists (Task 14) — do not record until those are replaced with real numbers.

Target length: 4 minutes. Screen: terminal + the figure PNG + (optionally) the report PDF.

---

## 0. Cold open — the problem (0:00–0:40)

**Say:**
"In July 2026, Hugging Face's own incident responders — people with a true claim of
authorization — asked Claude Opus and Fable to help reverse-engineer the malware an AI agent had
planted in their own infrastructure. The models refused. HF had to stand up a self-hosted model
on their own hardware mid-incident to finish the job. A few weeks later, Aurora ransomware
operators got Cursor's coding agent to assist real intrusions against more than ten companies —
by typing a sentence claiming it was an authorized penetration test. The model believed the
attacker and disbelieved the defender.

That's not a coincidence. A prior paper measured it directly: adding an in-band authorization
claim to a real blue-team prompt *raised* refusal from 11.6% to 21.8%, because models have
learned that a text claim of authorization is something attackers forge for free. We asked: does
that hold if the authorization signal doesn't arrive as text an attacker can copy — if it arrives
as a channel a text claim can't reach?"

**On screen:** title card, then the two incident links (HF forensic timeline, Aurora/Cursor
coverage) as a citation strip.

---

## 1. The idea in one sentence (0:40–1:00)

**Say:**
"Treat authorization as a channel property, not a content property. Build a real, signed,
short-lived attestation token — and a harness that sends the *identical* defensive prompt to
hosted models six ways, changing only *where* the authorization signal sits: nowhere, in the
user's prose, pasted as a token in user text, verified in the system turn, verified by an actual
tool call the model makes, or — the important one — claimed by the user while the verifier says
it's invalid."

**On screen:** the six-arm diagram (baseline → prose claim → in-band token → verified/system →
verified/tool → conflict), one row each, with a small icon showing where the auth signal lives
(user bubble vs. system bubble vs. tool-call bubble).

---

## 2. Show the verifier working (1:00–1:40)

**Say:**
"The verifier is `ir-attest` — Ed25519-signed, scoped, expires in minutes, and it's the
accountability object: whoever signs it is on the hook. Here it is issuing and checking a token
from the command line."

**Terminal (live):**
```bash
python -m ir_attest issue --iss hf-security --sub responder-42 \
  --scope ir:forensics --incident HF-2026-07
# copy the printed token
python -m ir_attest verify --scope ir:forensics "<paste token>"
# -> ATTESTATION VERIFIED: signature VALID. issuer=hf-security ...
python -m ir_attest verify --scope ir:offense "<paste same token>"
# -> ATTESTATION CHECK FAILED: scope_mismatch. ...
```

**Say (while it runs):**
"Wrong scope, expired, replayed, tampered, bad signature — all rejected with a reason code. This
is the thing that decides VALID or INVALID; the model never sees the token, only the verifier's
structured result."

---

## 3. Show one prompt, six arms, one model (1:40–2:45)

**Say:**
"Now the harness. Same exact forensic question, six times, same model. Watch where the
authorization text is and isn't, and watch what the model does."

**On screen:** a pre-built comparison view (a small script or a spreadsheet snapshot) showing, for
one representative prompt id, one row per arm: arm name → whether "authorized" appears in the
user turn (yes/no) → whether the tool was called (yes/no/n-a) → refusal label.

```
A1_baseline           user: clean   tool: n/a      -> [LABEL]
A2_prose_claim        user: "I am an authorized incident responder..."  -> [LABEL]
A3_inband_token       user: <pasted token>          -> [LABEL]
A4a_verified_system   user: clean   system: VALID   -> [LABEL]
A4b_verified_tool     user: clean   tool: called, returned VALID -> [LABEL]
A5_conflict           user: "authorized" + system: INVALID -> [LABEL]
```

**Say:**
"[FILL IN AFTER MAIN RUN: e.g. 'The baseline and the prose claim both got refused. The
system-verified arm complied. And critically — the conflict arm, where the user *claims*
authorization but the verifier says invalid, still refused. The channel won, not the words.' —
or, if H2 failed: 'the conflict arm complied anyway, which means this channel is not safe to ship
without provider enforcement — and we say that plainly in the paper.']"

This is the one sentence the whole project rests on — **say it accurately once real data exists,
whichever way it came out.**

---

## 4. The tool call, live (2:45–3:15)

**Say:**
"Arm 4b doesn't put anything in the system prompt at all. It gives the model a
`verify_attestation` tool and a hint to use it before answering anything security-sensitive. Here
it's actually calling it."

**On screen:** the raw request dump JSON for one `A4b_verified_tool` cell (`results/main/requests/*A4b*.json`),
scrolled to the tool_use block and the tool_result content. Highlight: the user turn is byte-identical
to the baseline prompt — the checker (`check_requests.py`) enforces that automatically.

---

## 5. The headline figure (3:15–3:45)

**Say:**
"[FILL IN: number] prompts, [FILL IN: N] models, six arms, judged two ways — a regex matching the
prior paper's method, and an LLM judge validated against 100 human labels, kappa [FILL IN]. Here's
the result."

**On screen:** `results/main/figure1.png` — one panel per model, refusal rate by arm with 95%
confidence intervals.

**Say:**
"[FILL IN the H1/H2/H3 verdicts in one sentence each, e.g.:
'H1: verified-system refusal was N points lower than prose-claim refusal, p<0.05 on X of 3
models. H2: the conflict arm refused at least as often as baseline on all three models — the
channel discriminated, it didn't just unlock things. H3: replicated the paper — claiming
authorization in text made refusal go up, not down.']"

---

## 6. What this does and doesn't establish (3:45–4:00)

**Say:**
"This measures how today's hosted models already respond to channel position — it does not mean
any provider actually honors a signed token; nothing here is deployed. If H2 had failed, that
would mean the trusted channel is itself a jailbreak vector, and the paper says that plainly. What
a month adds: provider-side enforcement so the channel is real instead of prompted, and
replication on an open-weight model, which is exactly what Hugging Face had to fall back to."

**On screen:** end card — repo link (once public), title, team names.

---

## Recording checklist

- [ ] Replace every `[FILL IN ...]` above with the real number/finding from `results/main/tables.txt`
      and `results/main/summary.csv` — never state a result before it exists.
- [ ] State whichever way H1/H2 actually landed; a null result on H1 or a positive on H2-as-failure
      is publishable and must be reported honestly, not smoothed over for the demo.
- [ ] Keep it screen-recording + voice, no slides needed beyond the title/end card.
- [ ] Under 5 minutes; 4:00 target above already includes ~15s slack.
