# attest-harness

Two small Python packages for the "AI Incident Response Sprint" attestation channel-position
experiment: `ir_attest` issues and verifies Ed25519-signed, scoped, short-lived incident-response
attestation tokens, and `attest_harness` runs a paired replay of identical prompts across six
authorization-channel arms (no claim, in-band prose claim, in-band token, verified system message,
verified tool call, and a conflicting claim-vs-verifier arm) against hosted LLM providers, scoring
refusals and producing statistics and a figure. See `docs/SPEC.md` for the full problem statement,
hypotheses, and design.

Install (editable, with dev/test extras):

```bash
pip install -e .[dev]
```

Run the test suite from the repo root (tests use cwd-relative `configs/` and `keys/`):

```bash
pytest
```

Run the experiment harness:

```bash
python -m attest_harness.runner --help
```
