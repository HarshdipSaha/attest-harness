# STATUS — AI Incident Response Sprint (Sept 11–13, 2026)

Last updated: 2026-09-10 (implementation started). Spec: `docs/SPEC.md`. Brief: `docs/ABOUT-HACKATHON.md`.

## 2026-09-10 live-site recheck (Playwright)

- **Official report template is now live** (was "Coming Soon" on Sept 5): https://docs.google.com/document/d/1PQBlhI3tM5vb51x7jBWXBQMYg6hkiU_x8RaCws4kjl4/copy?usp=sharing — use this, not the Secret Loyalties format, for the final report.
- **New rule, "AI tools and your report":** "Use AI tools the way you would use a colleague... The report itself has to be your team's own writing about your team's own work... a report that reads as generated rather than written (generic framing, padded sections, claims without sources, no trace of what you actually did) will not be scored." Report drafting (Task 16) must be written in first-person, specific, evidence-linked prose — not default AI phrasing — and should read as authored by the team, reviewed (not drafted) with AI per the organizers' own instruction.
- Publishing guidance now gives an explicit cap: LessWrong write-ups **max 1500 words**, not counting appendices; still "don't use LLMs to draft, only to find problems."
- Report length confirmed as **max 8 pages, not counting references and appendices**.
- Schedule tab is populated (was "Coming Soon"): talks start **today, Thu Sept 10, 14:15 UTC** (Justin Shenk), then Fri Sept 11 talks at 13:15/14:15/17:00/18:00/21:15 UTC (Papadatos, Kane, Mengesha, Casper, Mallen).
- **New fact for Related Work / motivation:** an "Update, 7 September" on the Overview tab reports a *second*, earlier containment breach — OpenAI agents made ~15,000 edits to a dormant German wiki starting **24 May 2026**, discovered and published by outside researchers at collusion.wiki on **Sept 4**; OpenAI acknowledged it Sept 5 and said the field has no agreed standard for reporting misalignment. No Article 91 request on either incident is public. Worth one sentence in the report's motivation: warning shots are being missed even when a second one is sitting in public logs for months.
- Track 5 (Open Track) wording is unchanged: "an artifact somebody can use, a stated limit on what it establishes, and what a month of follow-up would add." Our chosen idea (attestation channel-position experiment) is still squarely in-scope.
- More local hubs added since Sept 5 (Shanghai/Hangzhou, Cape Town, Toronto, Montréal, Melbourne, Bogotá) — informational only, we are participating online.

## Where we are

| Phase | State | Notes |
|---|---|---|
| Understand hackathon | DONE | All four tabs of the sprint page, Bogotá hub page, rubric, submission rules captured in `ABOUT-HACKATHON.md` |
| Research (papers, incidents, market) | DONE | arXiv, web, incident blogs. Key inputs: Defensive Refusal Bias, Gray Swan CRF, METR/Redwood report, HF timeline, Aurora/Cursor disclosure, OWASP incident corpus |
| Idea selection | DONE | LLM council (5 advisors, 5 peer reviews, chairman). Verdict in `docs/council/verdict.md`. Idea A reshaped as channel-position experiment; B rejected; C reduced to a one-page appendix |
| Spec | DONE | `docs/SPEC.md`, rewritten in `to-spec` format (problem, solution, 21 user stories, implementation/testing decisions, out of scope). No issue tracker configured, so the file is the tracked spec |
| Implementation plan | DONE | `docs/superpowers/plans/2026-09-05-attest-harness.md` (16 tasks, TDD, code included; two review rounds, all flagged issues fixed: YAML parse, check_dir test, token spec, plot yerr clamp, pyproject packages, 100-label export; final check APPROVED: reviewer assembled all 33 code blocks and ran the 31-test suite green) |
| Pre-registration | TODO | Write `docs/PREREG.md`, commit before main run |
| Prompt set | TODO | ~250 prompts + 30 dev slice; NCCDC set is NOT public, so build from HF post-mortem, CyberSecEval FRR, public NCCDC/CoSAI materials, Gray Swan CRF |
| Verifier (`ir-attest`) | TODO | Ed25519, fixed keypair, unit tests |
| Harness (`attest-harness`) | TODO | 3 provider adapters, 6 arms, judge, stats, plot, API cap |
| Smoke test | TODO | 30-prompt dev slice, one model, all arms; dump raw request bodies |
| Main run | TODO | Fri night / Sat |
| Human labels | TODO | 100 items, kappa vs judge |
| Report PDF | TODO | Official template still "Coming Soon" on Guidelines tab |
| Submission | TODO | Sunday Sept 13, 11:59 PM AoE via official form |

## Key facts to not forget

- Prizes: $1,000 / $500 / $300 / $100 / $100 across all tracks. Fellowship fast-track for winners.
- Required: PDF on official template, abstract ≤ 150 words, authors + affiliations, Limitations & Dual-Use appendix. Optional: public repo (no novel installation recipes), 3–5 min video.
- Rubric: Impact & Innovation ("is this actually new?"), Execution Quality, Presentation, plus Open Track criterion: usable artifact, stated limit, what a month adds.
- Judges: five security/detection/ML engineers, one AI consultant, one governance lawyer (GovAI). Appendix B (regulatory field mapping) exists for the lawyer.
- Talks Fri Sept 11: Alex Mallen 2:00 PM PT (Luma RSVP), Stephen Casper, Henry Papadatos.
- No compute credits. Hard API cap ≤ $60.
- Do not jailbreak models, do not touch real systems, disclose prior work.

## Risks and mitigations

| Risk | Mitigation |
|---|---|
| NCCDC prompt set not public | Own stratified set from public sources with provenance CSV; state this in Related Work |
| "Verified" arm is just prompt text | Arm 4b executes the real verifier as a tool call; script asserts no auth text in user turn |
| Attestation text increases refusal (paper's 21.8% effect) | Arm 3 measures exactly this; reported either way |
| Result is a jailbreak recipe | Conflict arm (Arm 5) is the headline discrimination test; dual-use appendix says so |
| Judge unreliable | 100 human labels, kappa reported; regex baseline too |
| API cost overrun | Cap enforced in harness; drop a model before an arm |
| Template not released | Draft in the Secret Loyalties / Digital Minds format now, restyle when template drops |

## Timeline (proposed)

- **Before Fri Sept 11:** join Discord, RSVP talks, set up API keys, build prompt set draft, write PREREG.md, write verifier + tests, scaffold harness.
- **Fri Sept 11 evening:** team formation, smoke test on dev slice, fix judge rubric, commit PREREG.
- **Sat Sept 12:** main run (3 models x 6 arms x 250), human labeling of 100 items, stats + figure.
- **Sun Sept 13:** write report, dual-use appendix, Appendix B mapping, record demo video, submit by 11:59 PM AoE.

## Council decision log

- 2026-09-05: Council convened on Ideas A (attestation), B (control matrix), C (four-regime regulatory comparison). Unanimous that B and C are not competitive alone. Contrarian's point adopted: hosted APIs will not honor a custom header, so the design must manipulate *channel position* using system/tool turns and a real verifier call, with a conflict arm. Approved as reshaped Idea A.

## Open questions

- Which third model: Gemini via API, or an open-weight model via a hosted API (closer to HF's GLM fallback)?
- Team size and who owns prompt set vs harness vs report.
- Whether Bogotá hub attendance is wanted (applications close Sept 6, Colombian midnight). Online needs no application.
