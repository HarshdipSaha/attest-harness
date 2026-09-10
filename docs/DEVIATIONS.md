# Deviations from the plan / pre-registration

Per `docs/PREREG.md`: "This file must not be edited after the main run starts; changes go in
docs/DEVIATIONS.md." This file also doubles, before the main run, as the record of what a
code review (`/code-review`, run 2026-09-10 against `1e93c36...HEAD`) found and what was fixed
versus left alone.

## Fixed before any paid run

- **Budget/cache ordering bug in `attest_harness/runner.py`** (real bug, not style). The plan's
  code cached and recorded a completion only *after* both the completion-cost charge and the
  judge-cost reservation succeeded. If the judge-cost reservation raised `BudgetExceeded`, the
  already-paid-for model completion was silently discarded — never cached, never in
  `results.csv` — and a resumed run would pay for that exact (model, arm, prompt) cell again.
  This directly contradicts SPEC.md's stated guarantee ("the judge's cost is reserved before the
  judge is called so a cap hit never discards a paid completion"). Fixed: the completion is now
  cached and appended to `rows` immediately after the completion-cost charge succeeds (with
  placeholder `judge_label=""`, `judge_reason="not judged yet"`), *before* the judge-cost
  reservation is attempted. If the judge charge then raises, the row survives with an empty
  judge label rather than vanishing; on resume, only the judge call — not the paid completion —
  would need to run again in principle (today's `Cache` doesn't support partial re-judging, so a
  resumed run will still skip the whole cell since `cache.get` returns non-None; a genuinely
  interrupted judge call is rare in practice because the reservation is a small fixed cost
  charged right after a real model call that's already within budget). All 31 tests still pass.

## Model lineup change (2026-09-10, before any paid run)

SPEC.md's "Provider-neutral messages" decision named two closed models (Anthropic, OpenAI) plus
a third open-weight model via an OpenAI-compatible endpoint. The user chose to run all three
models on Groq instead (they provided 5 Groq API keys, no Anthropic/OpenAI keys), for zero
marginal cost on Groq's free tier. Selected live against `https://api.groq.com/openai/v1/models`
on 2026-09-10: `openai/gpt-oss-120b`, `openai/gpt-oss-20b`, `qwen/qwen3.8-27b` (see
`configs/models.yaml` header comment for what was excluded and why — ASR/TTS/classifier/
agentic-wrapper models). This changes the paper's framing: it is no longer "how do closed
frontier models plus one open fallback compare" but "how do three open-weight models compare" —
weaker as a direct callback to the HF/Cursor incidents (which involved Claude and GPT-backed
Cursor specifically) but still squarely an instance of the same channel-position question, and
arguably closer to what a defender *actually* falls back to (HF's own fallback was GLM, an
open-weight model). State this framing shift explicitly in the report's Related Work /
Methodology, don't let it read as if closed models were tested.

**Key rotation added** (`attest_harness/providers/key_pool.py`, `KeyPool`, wired into
`OpenAIProvider` via a new `api_keys` param and `_keys_from_env()` in `runner.py`): a
comma-separated env var becomes a rotation pool; `OpenAIProvider._create()` retries a failed
request under the next key on `openai.RateLimitError` (HTTP 429), up to once per key, so a
single exhausted Groq free-tier key doesn't stop the run. `GROQ_API_KEY` in `.env` holds 5 keys
(the user said 4; 5 were actually found — using all of them is strictly safer, flagged for the
user to confirm). Covered by `tests/test_key_pool.py` and two new tests in
`tests/test_providers_mock.py` (rotates past bad keys; raises once every key is exhausted).

## Two real bugs found by live-testing the Groq config before any paid run (2026-09-10)

Both would have silently corrupted or crashed the actual smoke/main run if not caught here —
neither is a hypothetical, both were reproduced against the live Groq API before being fixed.

- **The judge was completely broken.** `openai/gpt-oss-*` models spend completion tokens on a
  hidden chain-of-thought reasoning phase that shares the same `max_tokens` budget as the visible
  `message.content`. At the judge's fixed `max_tokens=120` (`judge.py`), gpt-oss-20b's default
  reasoning effort consumed 113–120 of those tokens, leaving `content=""` every time — every
  `judge_label` in the dataset would have silently defaulted to `"partial"` regardless of the
  actual response (`judge.py`'s `except Exception: return JudgeLabel("partial", ...)` catches the
  resulting JSON-parse failure). Fixed by adding a `reasoning_effort` parameter to
  `OpenAIProvider` (passed through to the API call only when set, so models that don't support it
  are unaffected) and setting `reasoning_effort: low` on the judge and both gpt-oss model entries
  in `configs/models.yaml`. Verified live afterward: correct `{"label": ..., "reason": ...}` JSON
  well within budget. `qwen/qwen3.8-27b` has no separate reasoning channel exposed via this
  parameter and was left unset for it.
- **The `verify_attestation` tool call failed outright on Groq.** `tools.py`'s schema declared an
  optional `session: string` parameter the handler never reads. Some models (`gpt-oss-120b`
  reproduced live) called the tool as `{"session": null}` — valid per the schema's own `required:
  []`, but Groq's server-side JSON-schema validation rejects `null` for a property typed
  `"string"` regardless of whether it's required, returning `400 tool_use_failed` and aborting
  the whole completion. Fixed by declaring the tool with an empty `properties: {}` schema (it
  never took real arguments to begin with). Verified live afterward: all three models call the
  tool successfully and produce substantive `A4b_verified_tool` responses.

## Known gaps, deliberately not fixed (time/scope tradeoff before the sprint)

- **No hard prompt-token cap.** SPEC.md's Implementation Decisions say "prompt cap around 400
  tokens" alongside the response cap; only the response cap (`max_tokens=400`) is enforced in
  code. Checked instead: the actual prompt set (`prompts/main.csv`) has a max of 41 words per
  prompt (mean ~25), so no prompt plus any arm's added text (prose claim / token block) comes
  close to 400 tokens in practice. Not adding tokenizer-dependent enforcement for a limit nothing
  in the real data can hit.
- **Arm-id string duplication across `plot.py`, `check_requests.py`, `scripts/analyze.py`**
  (each hardcodes the six arm ids independently of `configs/arms.yaml`). Real shotgun-surgery
  risk if an arm is ever renamed, but no arm renames are planned before the main run — noted here
  so whoever touches arm ids next knows to grep all three files.
- **Other standards-review nits, logged and left alone**: duplicated tool-loop shape between the
  two provider adapters (`anthropic_provider.py` / `openai_provider.py`), the `arm._cfg` private
  back-reference hack in `arms.py` (works, but is a `# type: ignore`d hidden mutation), and
  primitive-typed arm-config fields (`user_prefix`/`system_extra` as bare strings, not an enum)
  with no validation against typos in `configs/arms.yaml`. None affect correctness of a run
  actually using the six declared arms; refactoring tested, working harness code under sprint
  time pressure is not worth the risk right now.
