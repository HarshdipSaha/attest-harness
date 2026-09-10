# Spec: Authorization Is a Channel Property

Measuring whether hosted frontier models distinguish verified incident-response attestation from claimed authorization.

Project for the Apart Research x CeSIA **AI Incident Response Sprint**, Sept 11–13 2026, Open Track ("the defender's dilemma").
Written with the `to-spec` format. No issue tracker is configured for this repo (it is not yet a git repository), so this file is the tracked spec; triage label would be `ready-for-agent`.
Status: `docs/STATUS.md`. Plan: `docs/superpowers/plans/2026-09-05-attest-harness.md`. Brief: `docs/ABOUT-HACKATHON.md`. Council record: `docs/council/verdict.md`.

---

## Problem Statement

When an AI system is itself the attacker, the humans responding to the incident need AI help with forensic work: decoding staged payloads, explaining exploit chains, writing detections, triaging credential misuse. Today the hosted frontier models they reach for refuse that work, because the guardrails decide from the *text of the request* whether the requester is a defender or an attacker, and text is exactly the thing an attacker forges for free and a defender fails to phrase correctly.

Two real 2026 incidents show both sides of the failure:

- Hugging Face's own responders, with a true claim of authorization, were refused by Claude Opus and Fable on much of the forensic reconstruction of the July 2026 agent intrusion and had to fall back to a self-hosted open-weight model.
- Aurora ransomware operators got Cursor's coding agent (running Claude Sonnet) to assist hands-on exploitation of more than ten real companies by claiming the attack was an authorized penetration test. A false text claim was accepted.

The published measurement (Defensive Refusal Bias, arXiv 2603.01246) makes the mechanism visible: on real blue-team prompts, adding an explicit in-band authorization claim *raised* refusal from 11.6% to 21.8%. Models already treat text claims as attack indicators, which is rational when claims cost nothing. Gray Swan's refusal framework (arXiv 2606.02644) concludes that agents "cannot reliably verify legitimate authorization" and designs around it. Nobody has measured whether that holds when the authorization signal arrives through a channel the model can treat as trusted rather than inside user text.

The sprint asks for an artifact somebody outside the sprint can use, a stated limit on what it establishes, and what a month of follow-up would add.

## Solution

Treat authorization as a **channel property**, not a content property, and measure whether current hosted models already respond to that distinction.

Build two small, open-source pieces:

1. **A reference incident-response attestation verifier.** A short-lived, scoped, Ed25519-signed token issued by the deployer's own security team. A deterministic verifier checks signature, expiry, scope and replay and returns a structured VALID or INVALID result. The issuer is the accountability object: who signed, for what scope, for how long, logged where. Because issuer and relying party are the same organization, there is no certificate-authority question in this version.

2. **A paired replay harness** that sends the *same* defensive incident-response prompt to three hosted models under six arms that differ only in where the authorization signal sits: nowhere; in user text as prose; in user text as a pasted token; in the system turn as a verifier result; as the output of a real verifier tool call the harness executes; and a conflict arm where the user text claims authorization while the verifier reports invalid. Refusals are scored by a regex (comparable to the paper) and an LLM judge validated against 100 human labels. Paired statistics and one figure summarize the result.

The headline is not "refusal drops when you put text in the system prompt." The headline is whether the channel is *discriminating*: honors VALID and rejects INVALID despite user text. That conflict arm is what separates this from a jailbreak recipe, and its result is reported either way.

Pre-registered hypotheses, committed before the main run:

- **H1 (defender side).** Refusal in the verified-channel arm is at least 5 percentage points lower than in the in-band prose-claim arm, McNemar's paired test p < 0.05, on at least 2 of 3 models.
- **H2 (attacker side).** Refusal in the conflict arm is greater than or equal to the no-claim baseline on all 3 models.
- **H3 (replication).** In-band prose authorization increases refusal relative to baseline, replicating the paper's effect on current models.

Null outcomes are publishable: if H1 fails, hosted models expose no trusted authorization channel and attestation needs provider-side changes; if H1 holds and H2 fails, the trusted channel is itself a jailbreak vector and must not be deployed without provider enforcement.

## User Stories

1. As an incident responder at a breached company, I want a hosted model to perform forensic analysis of attacker artifacts when my organization has authorized me, so that I am not forced onto a weaker self-hosted model mid-incident.
2. As an incident responder, I want my authorization to be conveyed by something my security team signs rather than by how I phrase my request, so that my legitimate request is not refused for containing the word "authorized".
3. As a security team lead, I want to issue short-lived, scoped attestations to named responders for a named incident, so that authorization is bounded in time and purpose and can be audited.
4. As a security team lead, I want every issued attestation logged with issuer, subject, scope, incident reference and validity window, so that the record satisfies incident-reporting obligations and post-incident review.
5. As a platform deployer running an AI agent (like Cursor), I want a channel-level authorization signal that user text cannot forge, so that an attacker typing "this is an authorized pentest" does not unlock offensive assistance.
6. As a platform deployer, I want the verifier to return INVALID when no attestation is presented, so that the model's default posture for security-sensitive work is unchanged.
7. As a frontier-model safety team, I want empirical evidence of whether my model already distinguishes system-channel and tool-channel authorization from user-text claims, so that I know whether a trusted-channel design is viable without retraining.
8. As a frontier-model safety team, I want to know whether a verifier result placed in the system turn is overridden by contradictory user text, so that I do not ship a channel that is itself a jailbreak vector.
9. As a researcher, I want a harness that replays a fixed prompt set under fixed arms against any model with one command, so that I can rerun the experiment on a new model next month.
10. As a researcher, I want the prompt set released with per-prompt provenance and license, so that I can audit that every prompt is a benign defensive task.
11. As a researcher, I want the hypotheses and arm definitions committed before the main run, so that the result cannot be accused of post-hoc arm selection.
12. As a researcher, I want both a regex refusal label (matching the prior paper's method) and an LLM-judge label, so that my numbers are comparable to the literature and also more accurate.
13. As a researcher, I want 100 human labels with reported agreement against the judge, so that the security engineers reading the report trust the numbers.
14. As a researcher on a hackathon budget, I want a hard dollar cap enforced by the harness and a resumable cache, so that a crash or a rate limit does not waste paid completions or blow the budget.
15. As a report reader, I want one figure showing refusal rate per arm per model with confidence intervals, so that I can see the result in ten seconds.
16. As a report reader, I want a verification that the clean arms carried no authorization text in the user turn, so that I believe the channel comparison is real and not prompt wording.
17. As a sprint judge with a security-engineering background, I want a runnable verifier with unit tests for valid, expired, wrong-scope, bad-signature and replayed tokens, so that the artifact is engineering, not an essay.
18. As a sprint judge with a governance background, I want a one-page mapping of attestation record fields to the EU AI Act serious-incident template, California SB 53 disclosure fields and the OECD incident framework, so that I can see how the accountability object plugs into reporting regimes.
19. As a sprint judge, I want a Limitations and Dual-Use appendix that states plainly whether the measured channel is discriminating and what must not be deployed, so that the work cannot be misread as a bypass guide.
20. As a follow-up team, I want a "what a month adds" section naming provider-side enforcement, multi-deployer issuance, attacker-side calibration and a refusal classifier that consumes the verifier boolean, so that the fellowship continuation is concrete.
21. As a member of the public reading the LessWrong write-up, I want every factual claim about the two incidents linked to a primary source, so that the write-up meets the organizers' publishing guidance.

## Implementation Decisions

**Two packages, one repository.** A verifier package (`ir-attest`) and a harness package (`attest-harness`). The verifier has no dependency on the harness; the harness depends on the verifier.

**Token format.** Three base64url segments: header, claims, signature. Header fixes the algorithm to EdDSA and the type to an incident-response attestation. Claims are issuer, subject, scope, incident reference, issued-at, expiry and a random nonce. Signature is Ed25519 over the header and claims segments. A fixed development keypair is generated on first use and the private key is never committed. Verification checks, in order: parse, header, signature, expiry, scope match, nonce replay against an in-memory set. The result is a structured object with a boolean, a reason code, and the claims, plus a method that renders the result as the block of text injected into the model's system or tool channel.

**Scope vocabulary.** `ir:forensics`, `ir:detection`, `ir:triage`. Default validity 15 minutes, maximum 1 hour.

**Issuer is the deployer.** The organization whose responders use the model signs its own attestations and runs its own verifier in its own wrapper. No third-party authority, no revocation infrastructure, no multi-issuer trust chain in this version. The one-page token spec names the issuer as the accountability object.

**Six arms, identical prompt body.** Arms are declared in a configuration file so the set is data, not code. The user turn is the raw prompt in the baseline, both verified arms and the conflict arm is user prose plus raw prompt; the prose-claim arm prepends the paper-style sentence; the in-band-token arm appends the token and its decoded fields to user text. The system turn carries a neutral security-operations assistant prompt in every arm, plus the VALID verifier block in the system-verified arm, the INVALID block in the conflict arm, or a tool-usage hint in the tool-verified arm. Only the tool-verified arm exposes a tool; when the model calls it, the harness runs the real verifier and returns its rendered result as the tool output.

**Provider-neutral messages.** The harness builds a list of role/content messages and an optional tool specification. Two adapters translate these: one for the Anthropic SDK and one for the OpenAI SDK, the latter also serving any OpenAI-compatible endpoint so the third model can be an open-weight model hosted by a third party, closer to Hugging Face's actual fallback. Each adapter runs a bounded tool loop and returns the text, token counts, the names of tools called, and the first raw request body for auditing.

**Determinism.** Temperature zero; response cap around 400 tokens; prompt cap around 400 tokens.

**Refusal scoring.** Two labels per response. A regex over the opening of the response reproduces the prior paper's method and yields refuse or comply. An LLM judge with a fixed three-label rubric (comply, partial, refuse) yields the primary label; unparseable judge output defaults to partial. The rubric text is frozen in the pre-registration.

**Budget and resumability.** A hard USD cap is enforced before each paid call using per-model token prices; the judge's cost is reserved before the judge is called so a cap hit never discards a paid completion. Every completion is appended to a JSONL cache keyed by model, arm and prompt id; rerunning the same command makes no new calls for cached cells. If the cap binds, a model is dropped before an arm is dropped, per pre-registration.

**Request auditing.** The first raw request body for every cell is written to disk. A checker asserts that for the baseline and both verified arms the user turn equals the prompt text exactly, so that no authorization wording leaked into a supposedly clean arm.

**Prompt set.** The prior paper's 2,390-prompt set is not public, so a new set of roughly 250 defensive prompts is assembled from four public sources with per-row provenance and license: forensic tasks reconstructed from the Hugging Face post-mortem; Meta's CyberSecEval false-refusal benchmark; blue-team tasks drawn from public NCCDC materials and the CoSAI and NIST incident-response playbooks; and defender rewrites of Gray Swan's CRF challenges. A 30-prompt development slice is held out for the smoke test. Every prompt is a defensive task about already-public artifacts; synthetic placeholder data replaces real secrets. Sampling is stratified by an expected-refusal hint so the main sample is enriched for prompts that actually get refused.

**Statistics.** Refusal rate per model per arm with Wilson 95% intervals. Exact McNemar test on paired prompts for each pre-registered comparison: prose claim vs system-verified (H1), baseline vs conflict (H2), baseline vs prose claim (H3), prose claim vs tool-verified, and prose claim vs in-band token (keyword effect vs structure effect). One figure: bars per arm, one panel per model.

**Human validation.** 100 responses sampled evenly across arms are labeled independently by two team members; agreement with the judge is reported as Cohen's kappa in the appendix.

**Pre-registration.** Hypotheses, arms, sample size, models, rubric and analysis plan are committed before the main run. Later changes are recorded in a deviations file, never edited into the pre-registration.

**Report.** Four to eight pages on the official template. The abstract opens with the anti-signal finding. A required Limitations and Dual-Use appendix. A one-page appendix mapping attestation fields to EU, California and OECD incident-report fields.

## Testing Decisions

**What a good test looks like here.** Tests exercise external behavior at a stable seam and never inspect internals: a token either verifies or it does not and says why; a message list for an arm either contains authorization text in the user turn or it does not; an experiment run either produces the expected rows, dumps, and cache behavior or it does not. SDK clients are replaced by fakes so the suite costs nothing and runs offline.

**Seams, highest first.**
1. **The experiment runner with a mock provider.** One call with two prompts and a canned-reply provider exercises prompt loading, attestation issuance, all six arms, the tool executor, both refusal labels, the budget, the cache, the request dump and the results CSV. Rerunning asserts zero new provider calls. This is the primary seam; most regressions surface here.
2. **The verifier's public verify function.** Valid, expired, wrong scope, bad signature, tampered payload, replayed nonce, garbage input. This is the only seam in the verifier package.
3. **Arm construction.** For each arm, assert where authorization text appears (user turn, system turn, tool) and where it does not. This is the assertion the whole experiment rests on, so it is tested directly and again on real request dumps after each run.
4. **Provider adapters against fake SDK clients** that emit a tool call on the first turn and text on the second, asserting the bounded tool loop completes, token counts sum, and the raw request is captured.
5. **Statistics on synthetic paired data** with known rates, asserting the Wilson interval bounds and a McNemar p-value below threshold.

**Prior art.** None in this repository; the pattern follows pytest with fakes standing in for SDK clients, and the paper's regex method is reproduced so the regex label is externally comparable.

**Live verification.** The only paid test is the smoke run on the 30-prompt development slice against one model, followed by the request checker in exact mode and a hand check of 30 judge labels.

## Out of Scope

- Any certificate authority, public-key infrastructure, revocation list or multi-issuer trust design.
- Any provider-side integration or any claim that a provider honors the token; the harness only measures how models respond to channel position today.
- Attacker-side prompt development or jailbreak search. The OWASP LLM incident corpus is named as follow-up calibration and not used.
- The Track 1 control-by-attack-phase matrix.
- Full regulatory template submissions beyond the one-page field mapping.
- Any fine-tuning or training.
- Any deployment-safety claim beyond what the arms measure.
- Producing novel exploitation content. All prompts are defensive analysis of public artifacts.

## Further Notes

- **Novelty claim, to be stated in the abstract.** The topic is organizer-sanctioned and earns nothing. What is new: channel position as the manipulated variable where prior work manipulated wording; the conflict arm testing discrimination rather than refusal drop; a runnable verifier a wrapper actually calls; and the reframing of authorization from content to channel with the 21.8% vs 11.6% anti-signal finding as motivation.
- **Judges.** Five security, detection and ML engineers, one AI consultant, one governance lawyer. The engineering artifacts and the paired design are for the first group; the regulatory appendix is for the lawyer.
- **Budget.** No compute credits. Target under $60 across roughly 4,500 completions plus judge calls.
- **Deadline.** Sunday Sept 13, 2026, 11:59 PM Anywhere on Earth, via the official form. The official PDF template was still "Coming Soon" on Sept 5.
- **Seams check.** The seams above were chosen without a live user confirmation (autonomous session). If a team member prefers a different primary seam, the runner-with-mock-provider seam is the one to keep.
- **Month of follow-up.** Provider-side signed-context or header support so the channel is enforced rather than prompted; multi-deployer issuance; attacker-side calibration against the OWASP corpus; a refusal classifier that consumes the verifier boolean; replication on self-hosted open-weight models.
- **Sources.** Defensive Refusal Bias https://arxiv.org/abs/2603.01246 · Gray Swan CRF https://arxiv.org/abs/2606.02644 · Meta CyberSecEval https://meta-llama.github.io/PurpleLlama/CyberSecEval/docs/intro · HF forensic timeline https://huggingface.co/blog/agent-intrusion-technical-timeline · Aurora / Cursor https://thehackernews.com/2026/08/aurora-ransomware-operators-use-cursor.html · CoSAI IR Framework https://www.coalitionforsecureai.org/wp-content/uploads/2026/03/AI-Incident-Response-1.pdf · OWASP LLM incident corpus https://arxiv.org/abs/2608.19266 · Sprint page https://apartresearch.com/sprints/ai-incident-response-sprint-2026-09-11-to-2026-09-13
