# MeshCFO Filing Radar

[![License: MIT](https://img.shields.io/badge/License-MIT-green.svg)](LICENSE)

**Cubiczan** night-watch for **DEMO** ICFR / restatement clocks: triage a
queue of fictional filing signals with a **local, open-weight model**,
rank the board, and deepen the critical cards into short Audit Committee
briefs. **Local-first by design: the default run makes no network calls
at all.** External services (Nebius Token Factory cloud models, Tavily
search) exist in the code but are **disabled by default** and run only
when explicitly enabled in configuration.

> **DEMO honesty:** the three issuers (`northstar`, `lumenbridge`,
> `cedarline`) are fictional Cubiczan DEMO companies. Every fixture is
> labeled DEMO in the fixture files, the CLI output, and the dashboard.
> Nothing here reads real EDGAR data. **This is a demo, not a
> production system** — see *Prior work & limitations* below.

## Quickstart

Verified on this machine (Python 3.12, 2 CPUs) on 2026-11-07:

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -e .            # add .[local] for in-process llama.cpp, .[dev] for pytest

# Default scan: LOCAL inference, external services off.
# Needs a GGUF model + a llama.cpp runtime (see "Local model" below).
meshcfo-radar scan --deep-all --out examples/nightpack-local.json

# Deterministic rules only (no model, works anywhere):
meshcfo-radar scan --offline --deep-all --out examples/nightpack-offline.json

# Dashboard (binds localhost only):
meshcfo-radar serve --port 18877
# open http://127.0.0.1:18877
```

No `.env` file and no API keys are needed for the default or offline runs.

## Local model

Default inference is **Qwen2.5-0.5B-Instruct (Q4_K_M GGUF, ~491 MB)**
running on CPU via llama.cpp:

| Setting | Default | Env var |
|---|---|---|
| Inference engine | `local` | `MESHCFO_INFERENCE` (`local` \| `offline` \| `live`) |
| Model file | `~/workspace/models/qwen2.5-0.5b-instruct-q4_k_m.gguf` | `MESHCFO_LOCAL_MODEL` |
| Helper fallback | `~/workspace/tools/local-llm/ask.py` | `MESHCFO_LOCAL_LLM_ASK_PY` |

How the local client works (`src/meshcfo_filing_radar/local_llm.py`):

1. **In-process** via `llama_cpp`, if the `llama-cpp-python` package is
   importable in the active environment (`pip install -e ".[local]"`).
2. **Subprocess fallback** to the `ask.py` helper, which runs the same
   GGUF model through its own llama-cpp-python venv. This is the path
   the verified run on this machine used, because the radar venv does
   not install `llama-cpp-python`.

What the model actually does: for each DEMO fixture it drafts the triage
JSON (severity, clock hours, owner seat, headline, rationale, deepen
flag) and, for cards that qualify, the deep-brief JSON (Audit Committee
one-liner, why-now, ICFR focus, next actions). The pipeline validates
and clamps every field (severity 1–10, length caps). If the model's
output for a card cannot be parsed or validated, that card falls back
to the deterministic rules in `offline.py`, and the fallback is recorded
in the pack's `notes` and in the card's own `mode`/`model_used` fields —
a card labeled `local` really was drafted by the local model.

Prompt note: the 0.5B model needs few-shot prompts. With placeholder-only
schemas it echoes a single value regardless of input (measured during
the rework); the shipped prompts include two contrasting worked
examples, after which it discriminates between signal types.

## External services — off by default

| Service | Purpose | Runs only when |
|---|---|---|
| Nebius Token Factory (Nemotron Nano / Lightning) | `live` inference engine | `MESHCFO_INFERENCE=live` **and** `MESHCFO_ENABLE_EXTERNAL=1` **and** `NEBIUS_API_KEY` set |
| Tavily Search | market context on cards (labeled, never EDGAR evidence) | `MESHCFO_ENABLE_EXTERNAL=1` **and** `TAVILY_API_KEY` set |

Keys present in the environment are **ignored** until
`MESHCFO_ENABLE_EXTERNAL=1` is set; the test suite pins this behavior.
See `.env.example` for the full variable list. Never commit API keys —
use `.env` (gitignored) or a mode-`600` key file.

## Demo assets

- Verified-run night pack (local inference): [`examples/nightpack-local.json`](examples/nightpack-local.json)
- Prior offline night pack: [`examples/nightpack-offline.json`](examples/nightpack-offline.json)
- Narrated demo video (< 60 s, built from the verified run): [`demo/meshcfo-filing-radar-demo.mp4`](demo/meshcfo-filing-radar-demo.mp4)
- Prior hackathon submission pack (frames, narration script, captions, thumbnail): [`submission/`](submission/) — **prior work, not submitted**; see disclosure below.

## Prior work & limitations

**Prior work disclosure.** This project was originally built in
October 2026 for the Nebius × NVIDIA Global AI Hackathon (see
`PLAN.md`, a historical planning document). The source archive imported
into this repository on 2026-11-07 already contained: the full pipeline
with Nebius Token Factory live inference and Tavily enrichment, the
three DEMO fixtures, the dashboard, tests, example night packs, and a
`submission/` folder with video frames, a narration script, captions,
and a thumbnail for a ~3-minute demo video. **That hackathon entry was
never submitted, and the ~3-minute video file itself was not present in
the archive** — only its frames/script/captions were. DEMO fixtures and
ICFR/RACI vocabulary were themselves adapted from the earlier Cubiczan
MeshCFO Control Tower project (also disclosed in `SUBMISSION.md`, a
draft that was never submitted).

**What changed in the 2026-11-07 rework:** default inference rewired
from the cloud Token Factory API to a local open-weight GGUF model via
llama.cpp; all external services gated behind an explicit opt-in
(`MESHCFO_ENABLE_EXTERNAL=1`) and off by default; JSON parsing hardened
(only objects accepted); DEMO labeling made explicit in fixtures, CLI,
and dashboard; setup instructions rewritten to match the verified run;
a new sub-60-second narrated demo video recorded from the verified
local run.

**Limitations — read before believing any output:**

- The local model is **Qwen2.5-0.5B**, a very small model chosen because
  it runs at usable speed on a 2-CPU box (~14 tokens/s). Its triage
  judgments are plausible drafts, not expert determinations. Concretely,
  in the verified 2026-11-07 run it rated all three DEMO signals
  severity 9 — including a material-weakness-only signal that the
  rule-based path rates 6 — and its deep briefs partly reuse the
  few-shot prompts' phrasing and occasionally drift into meta-commentary
  about the fixture text. Cards whose output cannot be parsed fall back
  to fixed rules (the fallback is labeled, per above). The 1.5B sibling
  model produces better text but ran at <1 token/s here, so it is not
  the default.
- All data is **fictional DEMO fixtures**. There is no EDGAR ingest, no
  real-time monitoring, and no alerting.
- The deterministic fallback encodes fixed severity rules per signal
  type; it is a demo heuristic, not a risk model.
- **Not production-ready.** No authentication on the dashboard API
  (localhost demos only), no persistence, no audit trail beyond the
  exported JSON, no evaluation against real filings. No claim of
  confidential computing is made: "local" means the model runs on this
  machine instead of a cloud API — nothing more.

## License

MIT © Cubiczan / Shyam Desigan
