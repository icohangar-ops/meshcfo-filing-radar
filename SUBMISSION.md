# Devpost submission draft — MeshCFO Filing Radar

> **STATUS: DRAFT ONLY — NEVER SUBMITTED, AND NOT TO BE SUBMITTED.**
> This document is retained as part of the project's prior-work record.
> The project was reworked local-first on 2026-11-07 (see README.md);
> the Nebius/Token Factory framing below describes the original
> October 2026 hackathon build, not the current default configuration.

**Hackathon:** [Nebius x NVIDIA Global AI Hackathon](https://nebiusglobalaihackathon.devpost.com/)  
**Do not submit until:** public GitHub URL + YouTube URL are ready, and live Token Factory key works for a recorded live run if judges test.

Copy fields into Devpost “Enter a Submission”.

---

## Project name
MeshCFO Filing Radar

## Tagline / Elevator pitch (≤ short blurb)
Cubiczan night-watch that triages a queue of DEMO ICFR/restatement signals with NVIDIA Nemotron Nano on Nebius Token Factory, deepens critical cards with Nemotron Lightning, and attaches Tavily market context — never as EDGAR evidence.

## Track
**Best Apps and Agents**  
(Also intend eligibility for **Best Use of Tavily** — runtime Tavily Search on every night pack.)

## Built with / Technologies
- Nebius Token Factory (`https://api.tokenfactory.nebius.com/v1/`)
- NVIDIA Nemotron 3 Nano (`nvidia/NVIDIA-Nemotron-3-Nano-30B-A3B`)
- NVIDIA Nemotron 3.5 Lightning (`nvidia/Nemotron-3_5-Lightning`)
- Tavily Search API
- Python 3.10+, FastAPI, Rich CLI
- DEMO EDGAR-style fixtures (fictional issuers)

## Inspiration
Office-of-the-CFO work is a **clock**, not a chatbot. Fractional CFOs and Controllers wake up to stacked DEMO Item 4.02 / Item 9A signals. We already built MeshCFO Control Tower (single-signal brief). Judges and operators also need a **queue**: what is critical tonight, what can wait, and where credits should buy deeper Nemotron reasoning.

## What it does
1. Loads three DEMO filing fixtures.
2. **Triages** each with Nemotron Nano (severity 1–10, regulatory clock hours, owner seat, deepen flag).
3. Optionally enriches with **Tavily** peer/market hits labeled `market_context` (never cited as EDGAR).
4. **Deepens** high-severity cards with Nemotron Lightning → Audit Committee one-liner, why-now, ICFR focus, next actions with seats + evidence.
5. Exports a ranked **night pack** JSON and shows it on a local radar board (`meshcfo-radar serve`).

## How we built it
Python package `meshcfo-filing-radar` with OpenAI-compatible client pointed at Token Factory, deterministic offline fallback, Tavily HTTP enrichment, FastAPI + static dashboard, and a ≤3 minute demo video.

## Challenges
Stored Token Factory API key returned HTTP 401 during build (rotation needed). Offline path + live Tavily kept the MVP demonstrable; live Nemotron path is implemented and retries cleanly after key rotate.

## Accomplishments
- Distinct second Nebius×NVIDIA entry vs Control Tower (queue + routing + Tavily).
- Dual-model Nemotron routing designed for credit efficiency.
- Working CLI + API + dashboard + submission pack.

## What we learned
Nano is enough for structured triage JSON; Lightning earns its tokens on deepen. Labeling Tavily as non-evidence is essential for ICFR honesty.

## What's next
Live EDGAR ingest (still DEMO-gated for demos), Nebius Serverless Jobs for overnight scans, and push notifications to Controller seat.

## Try it out / Demo URL
Local: `meshcfo-radar serve --port 18877` → http://127.0.0.1:18877  
(Sample night pack: `examples/nightpack-offline.json`)

## Public repo URL
_(pending publish — do not publish in this task)_  
Suggested: `https://github.com/Cubiczan/meshcfo-filing-radar`

## Demo video URL
_(pending YouTube upload)_  
Local file: `submission/meshcfo-filing-radar-demo.mp4`

## Image / thumbnail
`submission/thumbnail-1280x720.png`

## How NVIDIA Nemotron + Token Factory accelerated the workflow
Token Factory’s OpenAI-compatible API let us ship Nano triage and Lightning deepen behind one client. Routing keeps everyday cards on Nano and spends Lightning only when severity warrants it.

## Feedback on Nebius Token Factory / AI Cloud / NVIDIA tools
Token Factory model catalog and Nemotron open weights are excellent for finance-agent demos. Pain point: API keys can 401 after idle periods without a clear in-product rotate nudge; a “test key” button on the keys page would help hackathon builders. Nemotron JSON discipline is strong when thinking traces are disabled via `chat_template_kwargs`.

## Pre-existing project updates (if asked)
Control Tower existed as a separate submission. Filing Radar is **new** during the Submission Period: new product surface (queue), new Nano→Lightning router, Tavily path, dashboard, and packaging. Shared only DEMO fixtures / ICFR vocabulary (disclosed).

## Team
| Field | Value |
|---|---|
| Name | Shyam Desigan |
| Org | Cubiczan |
| Role | Solo |
| Email | sam@cubiczan.com |
