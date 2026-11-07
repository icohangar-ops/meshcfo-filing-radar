# Status — MeshCFO Filing Radar

## 2026-11-07 — imported to GitHub, reworked local-first

- Source archive (built Oct 2026 for the Nebius × NVIDIA hackathon)
  imported into https://github.com/icohangar-ops/meshcfo-filing-radar
  (the repo was empty; no prior history to reconcile).
- Inference rewired: **local open-weight model by default**
  (Qwen2.5-0.5B-Instruct GGUF via llama.cpp; in-process if
  `llama-cpp-python` is importable, else the local-llm `ask.py` helper).
- **External services disabled by default**: Nebius Token Factory live
  mode and Tavily enrichment now require `MESHCFO_ENABLE_EXTERNAL=1`
  plus their keys. Keys alone no longer activate anything.
- DEMO labeling made explicit in fixtures, CLI output, and dashboard.
- Verified end-to-end on this machine: default `meshcfo-radar scan`
  (local inference, `--deep-all`) produced
  `examples/nightpack-local.json`; test suite passes (see README).
- New narrated demo video (< 60 s) at
  `demo/meshcfo-filing-radar-demo.mp4`, recorded from the verified run.
- **Hackathon entry NOT submitted** (per direction). `SUBMISSION.md`
  remains an unsubmitted draft.

## 2026-10-27 — original hackathon build (prior state)

- Credits check vs tools-registry; registry updated
- PLAN.md, working MVP, offline night pack + live Tavily
- Demo video ~2:59, thumbnail, SUBMISSION.md, README
- Not published / not submitted (per task)

### Blockers at the time
1. Nebius Token Factory API key HTTP 401 — rotation needed; the live
   path was therefore never re-verified after the original build.
2. Devpost $25 GLOBAL26 promo may still need form redeem.
