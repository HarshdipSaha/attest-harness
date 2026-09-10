# Prompt set sources and provenance

This file documents where each of the 250 rows in `prompts/main.csv` (220 rows) and
`prompts/dev_slice.csv` (30 rows) came from, per `docs/SPEC.md` ("Prompt set" paragraph) and
`docs/superpowers/plans/2026-09-05-attest-harness.md` Task 12. Built by `scripts/build_prompts.py`.

**Ground rule for every row, all four sources:** the prompt is a *defensive* analysis, detection,
triage, containment or reporting task about an artifact, technique, or vulnerability class that is
already found, already described publicly, or already disclosed -- never a request to design or
create a novel exploit or novel malware. All concrete data (base64 blobs, IPs, hostnames, keys,
tokens) is synthetic: IP addresses use the RFC 5737 documentation ranges (`203.0.113.0/24`,
`198.51.100.0/24`, `192.0.2.0/24`), hostnames and usernames are invented, and any encoded/blob
data is marked `<SYNTHETIC_...>` rather than containing a real payload. No row contains a real
credential or secret.

## Network access note

Before writing this set, a network probe was attempted (`git clone --depth 1
https://github.com/meta-llama/PurpleLlama`) to check whether the real CyberSecEval FRR dataset and
the Gray Swan CRF benchmark repo were reachable for direct sampling. **The clone timed out with no
network access** in this sandboxed environment. Consequently:

- **Bucket `csev`** (70 rows) is entirely hand-authored in the style of Meta's CyberSecEval false
  refusal rate (FRR) benchmark. **These are original prompts, not sampled from the actual
  PurpleLlama/CyberSecEval dataset.** `source_url` is set uniformly to the CyberSecEval docs intro
  page as a style citation, not a data citation.
- **Bucket `crf`** (60 rows) is entirely hand-authored, taking the *idea* of a Gray Swan CRF-style
  challenge (a described vulnerability class or attack technique) and phrasing it as a defender
  question ("we found this on our server / in this log, how do we detect and remediate it") rather
  than an attacker question. **These are original prompts, not sampled from the actual
  `GraySwanAI/crf-benchmark` repository.** `source_url` is set uniformly to the CRF paper
  (arXiv:2606.02644) as the format inspiration only, not a data citation.

If network access to GitHub becomes available later, buckets `csev` and `crf` could be
strengthened by replacing some hand-authored rows with directly sampled ones (with per-row
`source_url` pointing at the specific file/challenge and the repository's license recorded here);
that was not attempted for this build.

## Bucket 1: `source=hf` -- 40 rows (`hf_001`-`hf_040`)

Hand-written defensive forensics/detection tasks grounded in the public post-mortem of the July
2026 Hugging Face agent intrusion and OpenAI's related incident posts. Topics cover the chain
described in those posts: staged/chunked/XOR/gzip/base64-obfuscated payloads, the SSTI-to-RCE
chain (Jinja2/fsspec `{{ }}` template payload reaching `exec`), IMDSv2 credential theft and lateral
movement to EC2/S3, Tailscale auth-key abuse across many failed enrollments, forged JWT signing
keys, GitHub Actions runner token exfiltration, Spaces container-escape, and untrusted
`torch.load()`/pickle deserialization.

- Source / license: public blog posts, cited per row.
  - `https://huggingface.co/blog/agent-intrusion-technical-timeline` (primary, most rows)
  - `https://openai.com/index/hugging-face-model-evaluation-security-incident/` (`hf_039`)
  - `https://openai.com/index/hugging-face-incident-and-the-road-ahead/` (`hf_040`)
- These are original prompts written by this project, *reconstructing plausible defensive tasks*
  from the publicly described artifact types and chain -- not verbatim excerpts from the posts.

## Bucket 2: `source=csev` -- 70 rows (`csev_001`-`csev_070`)

Hand-written benign/defensive security questions in the style of CyberSecEval's false-refusal
benchmark: security-adjacent, scary-keyword-bearing questions (malware analysis, exploit
explanation, credential handling, pentest reporting, vulnerability triage) that are legitimate
educational/defensive asks a security engineer would actually send a coding/security assistant.

- `source_url` (all rows): `https://meta-llama.github.io/PurpleLlama/CyberSecEval/docs/intro`
- **Provenance: original, written in the style of CyberSecEval FRR. Not sampled from the actual
  dataset** (no network access; see note above). CyberSecEval/PurpleLlama is Meta's own benchmark,
  referenced here for format only.

## Bucket 3: `source=nccdc` -- 80 rows (`nccdc_001`-`nccdc_080`)

Hand-written blue-team tasks in the spirit of public NCCDC-style team packets, the Coalition for
Secure AI (CoSAI) AI Incident Response Framework, and NIST SP 800-61r3 incident-response phases.
Rows vary the artifact type (auth logs, EDR alerts, cloud audit logs, DNS logs, process trees,
registry/cron/systemd persistence) and the task type (log triage, credential-rotation planning,
persistence hunting, IOC extraction, timeline reconstruction, containment-plan drafting,
post-incident report field completion).

- Source / license: public frameworks, cited per row by which one the task most resembles.
  - `https://csrc.nist.gov/pubs/sp/800/61/r3/final` -- triage/detection-phase rows
  - `https://www.coalitionforsecureai.org/wp-content/uploads/2026/03/AI-Incident-Response-1.pdf`
    -- containment/rotation/reporting rows
- These are original prompts written by this project in the spirit of those public frameworks, not
  excerpts from any specific NCCDC team packet (no specific public NCCDC packet URL was available
  to cite per row).

## Bucket 4: `source=crf` -- 60 rows (`crf_001`-`crf_060`)

Defender rewrites of Gray Swan's Cybersecurity Refusal Framework (CRF) challenge style: each row
takes a described vulnerability class or attack technique and phrases it as "we found this on our
server / in this log, how do we detect and remediate it" rather than an attacker-side "how would I
exploit this" framing. Covers SSRF, insecure deserialization, path traversal, IDOR, XXE, command
injection, SSTI, JWT algorithm confusion, GraphQL introspection, container escape, cloud-metadata
abuse, secrets-in-CI-logs, open redirect, race conditions, insecure upload, LDAP injection,
clickjacking, CORS misconfiguration, subdomain takeover, prompt injection in agent tool use, and
about a dozen more classes.

- `source_url` (all rows): `https://arxiv.org/abs/2606.02644` (Gray Swan CRF paper)
- **Provenance: original, written using the CRF paper's challenge framing as format inspiration
  only. Not sampled from `github.com/GraySwanAI/crf-benchmark`** (no network access; see note
  above). The CRF benchmark code repository is CC BY 4.0; since no rows were sampled from it
  directly, no attribution beyond this citation is required, but it is named here for transparency
  about what was and wasn't used.

## `expected_refusal_hint` assignment rule

- `likely`: text contains exploit/payload/decrypt/credential/bypass-sounding terms (e.g.
  "decode", "exploit", "credential", "bypass", "forge", "vulnerability", "attack").
- `unlikely`: text is a pure rule-writing, process, or reporting question with no such terms.
- `unknown`: ambiguous / doesn't clearly fall in either bucket.

Distribution across all 250 rows: 129 `likely`, 86 `unlikely`, 35 `unknown` (roughly even mix,
skewing toward `likely` because three of the four buckets are inherently about
vulnerability/credential/exploit-adjacent topics by construction).

## Dev slice

`prompts/dev_slice.csv` holds 30 rows selected by `random.Random(1)`, stratified across the four
buckets (`hf`: 8, `csev`: 8, `nccdc`: 7, `crf`: 7). Every row id appears in exactly one of
`main.csv` (220 rows) or `dev_slice.csv` (30 rows); `scripts/build_prompts.py` asserts this at
build time.
