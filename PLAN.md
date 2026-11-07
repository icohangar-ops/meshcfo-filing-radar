# MeshCFO Filing Radar — Nebius × NVIDIA plan

> *Historical planning document from the original October 2026
> hackathon build. Retained for prior-work disclosure. For the current
> state of the project (local-first inference, external services off by
> default), see README.md and STATUS.md.*

**Hackathon:** [Nebius x NVIDIA Global AI Hackathon](https://nebiusglobalaihackathon.devpost.com/)  
**Deadline:** Fri Oct 30, 2026 **1:00 PM ET** (= 10:00 AM PDT)  
**Builder:** Shyam Desigan / Cubiczan (solo)  
**Track (chosen):** **Best Apps and Agents** (also targeting **Best Use of Tavily** $3k bonus)  
**Working title:** **MeshCFO Filing Radar**

---

## Credits / resources check (done before build) — 2026-10-27 ~8:00 AM ET

Logged in `/workspace/contests/tools-registry.md`.

| Resource | Amount | Status |
|---|---|---|
| Nebius Token Factory (Builders) | $25 | **SECURED** Sep 5 (balance +$25 to ~$124.73) |
| Nebius Token Factory (Devpost form) | $25 code `NEBIUS-DEVPOST-GLOBAL26` | **NEEDS BROWSER** — form/redeem may still be unused; stored key returns **HTTP 401** |
| Nebius Builders Program | TF $25 + Tavily $25 + extras | **SECURED** (welcome Sep 5; Tavily add-on present) |
| Tavily API | existing Project + Builder add-on | **LIVE** confirmed 2026-10-27 |
| Stored TF API key | `/home/box/.config/pipeline/nebius.tokenfactory.key` | **BLOCKED — 401 Unable authenticate** |

**Browser claim URL (exact):**  
https://nebius.com/promo-code?utm_promo_event_code=2026-devpost-global-ai-hack&utm_promo_code_type=Token_Factory&utm_promo_activation_code=NEBIUS-DEVPOST-GLOBAL26  

Activation code to enter: `NEBIUS-DEVPOST-GLOBAL26`  
Then: Token Factory console → create/rotate API key → save to key file.

Builders join (already done historically): https://dev.nebius.com/builders  
Resources page: https://nebiusglobalaihackathon.devpost.com/resources

---

## Why this idea (distinct from MeshCFO Control Tower)

Control Tower already exists as a Nebius × NVIDIA **Best Apps and Agents** entry: one DEMO signal → one governed remediation brief with CHP lock.

**Filing Radar is a different product surface:**

1. **Night-watch queue** — triage *multiple* DEMO filing signals into a ranked risk board (not a single brief).
2. **Dual-Nemotron routing on Token Factory** — **Nano** for fast severity/clock triage; **Lightning** for deep why-now + Audit Committee one-liner when severity ≥ threshold.
3. **Tavily market context** (labeled, never as EDGAR evidence) — qualifies for **Best Use of Tavily**.
4. **Operator UX** — CLI `radar scan` + local dashboard showing triage cards → deepen one issuer → export night pack JSON.

Reuses Cubiczan DEMO fixtures / ICFR ownership vocabulary (disclosed). Does **not** copy Control Tower's CHP lock pipeline as the primary artifact.

---

## Eligibility gates (must not break)

From Official Rules:

- Runtime call to **Nebius Token Factory** OR deploy on Nebius AI Cloud.
- Use ≥1 **NVIDIA open model** (Nemotron Nano + Lightning).
- Public OSS repo + README highlighting Nemotron + Token Factory.
- Demo video ≤ 3 min on YouTube; working demo URL; track identified; feedback section.
- If prior work existed: explain significant updates during Submission Period.
- Multiple submissions OK if unique and substantially different.

---

## Architecture

```
DEMO fixtures (3 issuers)
        │
        ▼
  Nano triage (Token Factory)  ──► severity, clock hours, owner seat guess
        │
        ├─ Tavily search (market/peer context, labeled)
        │
        ▼
  Lightning deepen (if severity high / --deep-all)
        │
        ▼
  Night pack JSON + HTML radar board
```

Offline mode: deterministic triage + deepen stubs so judges can run without a key; live mode preferred when key works.

---

## Build deliverables (this folder)

- Working MVP under `/workspace/contests/nebius-nvidia/`
- `PLAN.md` (this file)
- Public-ready repo (no secrets) — **do not publish yet**
- ~3 min FFmpeg demo (1920×1080, real footage + TTS + captions)
- 1280×720 thumbnail
- `SUBMISSION.md` with Devpost fields
- **Do not submit** to Devpost in this task

---

## Prior work disclosure (for SUBMISSION.md)

DEMO fixtures and ICFR/RACI vocabulary adapted from Cubiczan MeshCFO Control Tower. Built for this hackathon: multi-signal radar queue, Nano→Lightning routing, Tavily enrichment path, night-pack export, dashboard, video/submission pack.
