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
