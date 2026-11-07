"""Filing Radar pipeline: triage → optional Tavily → deepen.

Inference engines:
- "local" (DEFAULT): open-weight GGUF model on this machine via
  llama.cpp (local_llm.LocalModelClient). No network calls.
- "offline": deterministic rules (offline.py). No model, no network.
- "live": Nebius Token Factory cloud models. EXTERNAL — runs only when
  MESHCFO_ENABLE_EXTERNAL=1 and a Nebius key is configured.

Tavily market enrichment is also external and off by default; it runs
only with MESHCFO_ENABLE_EXTERNAL=1 and a Tavily key.

Any engine failure on a card falls back to the deterministic offline
rules for that card, and the fallback is recorded in the pack notes and
in the card's mode/model_used fields — nothing is silently relabeled.
"""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Literal

from meshcfo_filing_radar.config import Settings, get_settings
from meshcfo_filing_radar.fixtures_loader import load_all, load_fixture
from meshcfo_filing_radar.llm import TokenFactoryClient, TokenFactoryError
from meshcfo_filing_radar.local_llm import LocalLLMError, LocalModelClient
from meshcfo_filing_radar.offline import offline_deepen, offline_triage
from meshcfo_filing_radar.schemas import DeepBrief, NightPack, SignalFixture, TriageCard
from meshcfo_filing_radar import tavily_enrich


TRIAGE_SYSTEM = """You are MeshCFO Filing Radar triage (office of the CFO).
Return JSON ONLY with keys:
severity (int 1-10), clock_hours (int), owner_seat (string),
triage_headline (string <= 120 chars), why_triage (string <= 400 chars),
deepen_recommended (bool).
Rules: DEMO issuers only; do not invent real executives; treat excerpts as DEMO FILING TEXT.
Severity 9-10 = active non-reliance / restatement clock; 7-8 = MW needing board attention.
"""


DEEPEN_SYSTEM = """You are MeshCFO Filing Radar deepen.
Return JSON ONLY with keys:
ac_one_liner (string), why_now (string), icfr_focus (array of strings),
next_actions (array of strings), provenance_note (string).
Rules: ownership language (RACI seats), no invented named people, DEMO honesty,
next_actions must name a seat + evidence. Market hits are context only — never cite as EDGAR.
"""


# Prompts for the small local model. Few-shot examples are REQUIRED:
# with placeholder-only schemas, Qwen2.5-0.5B echoes a single value or a
# literal "1"; two contrasting worked examples make it actually rate
# the input (verified on this machine, 2026-11-07).
LOCAL_TRIAGE_SYSTEM = """You triage DEMO company filing signals for a CFO office.
Reply with ONE JSON object with keys: severity (int 1-10), clock_hours (int),
owner_seat, triage_headline, why_triage, deepen_recommended (true/false).
Severity guide: 9-10 = non-reliance / restatement clock; 7-8 = material
weakness needing board attention; 5-6 = elevated ICFR signal.
Examples of the reply format:
{"severity": 9, "clock_hours": 72, "owner_seat": "Controller (R) / CFO (A)", "triage_headline": "ACME-DEMO: non-reliance clock — triage CRITICAL", "why_triage": "DEMO Item 4.02 non-reliance plus material weakness; amendment clock is active.", "deepen_recommended": true}
{"severity": 6, "clock_hours": 168, "owner_seat": "SOX PMO", "triage_headline": "BETA-DEMO: MW / ICFR signal — elevated", "why_triage": "DEMO material-weakness disclosure; remediation testing plan needed.", "deepen_recommended": false}
Rate the filing in the user message the same way, using ITS facts.
DEMO issuers only; do not invent people. No text outside the JSON."""

LOCAL_DEEPEN_SYSTEM = """You write a short Audit Committee brief for a DEMO filing signal.
Reply with ONE JSON object with keys: ac_one_liner, why_now,
icfr_focus (array of 2-3 strings), next_actions (array of 2-3 strings,
each "Seat: action"), provenance_note.
Example of the reply format:
{"ac_one_liner": "DEMO: Acme Corp needs a Controller-owned remediation plan for revenue cutoff before the next periodic report.", "why_now": "The DEMO non-reliance determination started an amendment and certification clock.", "icfr_focus": ["Design vs operating: revenue cutoff", "Evidence: journals and hold-criteria documents"], "next_actions": ["Controller: inventory affected periods", "IA: schedule interim remediation test"], "provenance_note": "Drafted by a local open-weight model from DEMO fixture facts."}
Write the brief for the filing in the user message, using ITS facts.
Name RACI seats (Controller, CFO, IA); never invent named people.
No text outside the JSON."""


def _fixture_user_blob(fixture: SignalFixture, *, compact: bool = False) -> str:
    if compact:
        excerpts = "\n".join(
            f"- [{ex.source_id}] {ex.locator}: {ex.excerpt[:200]}" for ex in fixture.excerpts[:2]
        )
    else:
        excerpts = "\n".join(
            f"- [{ex.source_id}] {ex.locator}: {ex.excerpt[:280]}" for ex in fixture.excerpts[:4]
        )
    facts = "; ".join(f"{k}={v}" for k, v in fixture.structured_facts.items())
    return (
        f"fixture_id={fixture.fixture_id}\n"
        f"company={fixture.company.display_name} ticker={fixture.company.ticker}\n"
        f"signal_kind={fixture.signal_kind} filed_on={fixture.filed_on}\n"
        f"facts: {facts}\n"
        f"excerpts:\n{excerpts}\n"
        f"disclaimer: {fixture.demo_disclaimer}"
    )


def _model_triage(
    client,
    fixture: SignalFixture,
    model: str,
    mode: Literal["live", "local"],
    settings: Settings,
) -> TriageCard:
    local = mode == "local"
    payload = client.complete_json(
        model=model,
        system=LOCAL_TRIAGE_SYSTEM if local else TRIAGE_SYSTEM,
        user=_fixture_user_blob(fixture, compact=local),
        max_tokens=settings.local_max_tokens_triage if local else 512,
    )
    severity = int(payload.get("severity") or 5)
    severity = max(1, min(10, severity))
    return TriageCard(
        fixture_id=fixture.fixture_id,
        company=fixture.company.display_name,
        ticker=fixture.company.ticker,
        signal_kind=fixture.signal_kind,
        filed_on=fixture.filed_on,
        severity=severity,
        clock_hours=int(payload.get("clock_hours") or 168),
        owner_seat=str(payload.get("owner_seat") or "Controller"),
        triage_headline=str(payload.get("triage_headline") or f"{fixture.company.ticker} triage")[:160],
        why_triage=str(payload.get("why_triage") or "")[:500],
        deepen_recommended=bool(payload.get("deepen_recommended", severity >= 7)),
        model_used=model,
        mode=mode,
    )


def _model_deepen(
    client,
    fixture: SignalFixture,
    model: str,
    mode: Literal["live", "local"],
    market_blob: str,
    settings: Settings,
) -> DeepBrief:
    local = mode == "local"
    user = _fixture_user_blob(fixture, compact=local) + "\nmarket_context (NOT evidence):\n" + market_blob
    payload = client.complete_json(
        model=model,
        system=LOCAL_DEEPEN_SYSTEM if local else DEEPEN_SYSTEM,
        user=user,
        max_tokens=settings.local_max_tokens_deepen if local else 900,
    )
    default_prov = (
        f"Local open-weight model ({model}) running on-device via llama.cpp; "
        "DEMO fixture, no external calls."
        if local
        else "Nemotron deepen on Token Factory"
    )
    return DeepBrief(
        fixture_id=fixture.fixture_id,
        ac_one_liner=str(payload.get("ac_one_liner") or "")[:400],
        why_now=str(payload.get("why_now") or "")[:600],
        icfr_focus=[str(x) for x in (payload.get("icfr_focus") or [])][:6],
        next_actions=[str(x) for x in (payload.get("next_actions") or [])][:8],
        provenance_note=str(payload.get("provenance_note") or default_prov)[:400],
        model_used=model,
        mode=mode,
    )


# Backwards-compatible wrappers (original live-mode API).
def live_triage(client: TokenFactoryClient, fixture: SignalFixture, model: str) -> TriageCard:
    from meshcfo_filing_radar.config import get_settings as _gs

    return _model_triage(client, fixture, model, "live", _gs())


def live_deepen(client: TokenFactoryClient, fixture: SignalFixture, model: str, market_blob: str) -> DeepBrief:
    from meshcfo_filing_radar.config import get_settings as _gs

    return _model_deepen(client, fixture, model, "live", market_blob, _gs())


def run_radar(
    *,
    fixture_ids: list[str] | None = None,
    offline: bool = False,
    deep_all: bool = False,
    use_tavily: bool = True,
    settings: Settings | None = None,
    mode: str | None = None,
) -> NightPack:
    settings = settings or get_settings()
    fixtures = (
        [load_fixture(i) for i in fixture_ids]
        if fixture_ids
        else load_all()
    )

    notes: list[str] = []
    mode_flags: set[str] = set()

    requested = (mode or settings.inference_mode or "local").strip().lower()
    if offline:
        requested = "offline"
    if requested not in {"local", "live", "offline"}:
        notes.append(f"Unknown inference mode '{requested}' — using local.")
        requested = "local"

    live_client: TokenFactoryClient | None = None
    local_client: LocalModelClient | None = None

    if requested == "live":
        if not settings.live_llm_ready:
            if not settings.enable_external_services:
                notes.append(
                    "Live mode requested but external services are disabled by default "
                    "(MESHCFO_ENABLE_EXTERNAL is not 1) — using local inference."
                )
            else:
                notes.append(
                    "Live mode requested but no NEBIUS_API_KEY found — using local inference."
                )
            requested = "local"
        else:
            try:
                live_client = TokenFactoryClient(settings)
            except TokenFactoryError as e:
                notes.append(f"Token Factory client init failed → local: {e}")
                requested = "local"

    if requested == "local":
        try:
            local_client = LocalModelClient(settings)
            notes.append(
                f"Local inference: {local_client.model_label} via llama.cpp "
                "(open-weight GGUF, on-device, no network)."
            )
        except LocalLLMError as e:
            notes.append(f"Local model unavailable → offline deterministic: {e}")
            requested = "offline"

    if requested == "offline" and offline:
        notes.append("Forced --offline: deterministic triage/deepen (no model called).")

    cards: list[TriageCard] = []
    tavily_skip_noted = False
    for fx in fixtures:
        card: TriageCard
        if requested == "live" and live_client is not None:
            try:
                card = _model_triage(live_client, fx, settings.nebius_triage_model, "live", settings)
                mode_flags.add("live")
            except TokenFactoryError as e:
                notes.append(f"Live triage failed for {fx.fixture_id}: {e}; using offline.")
                card = offline_triage(fx)
                mode_flags.add("offline")
        elif requested == "local" and local_client is not None:
            try:
                card = _model_triage(local_client, fx, local_client.model_label, "local", settings)
                mode_flags.add("local")
            except LocalLLMError as e:
                notes.append(f"Local triage failed for {fx.fixture_id}: {e}; using offline.")
                card = offline_triage(fx)
                mode_flags.add("offline")
        else:
            card = offline_triage(fx)
            mode_flags.add("offline")

        if use_tavily:
            if settings.tavily_allowed:
                try:
                    card.market_hits = tavily_enrich.search_market_context(
                        settings.resolved_tavily_key(), fx
                    )
                except Exception as e:  # noqa: BLE001
                    notes.append(f"Tavily failed for {fx.fixture_id}: {e}")
            elif settings.resolved_tavily_key() and not tavily_skip_noted:
                notes.append(
                    "Tavily key present but external services are disabled by default — "
                    "enrichment skipped. Set MESHCFO_ENABLE_EXTERNAL=1 to enable."
                )
                tavily_skip_noted = True
        cards.append(card)

    deep_briefs: list[DeepBrief] = []
    for fx, card in zip(fixtures, cards):
        if not (deep_all or card.deepen_recommended or card.severity >= settings.deepen_severity_threshold):
            continue
        market_blob = "\n".join(
            f"- {h.title}: {h.snippet[:160]} ({h.url})" for h in card.market_hits
        ) or "(none)"
        brief: DeepBrief
        if card.mode == "live" and live_client is not None:
            try:
                brief = _model_deepen(live_client, fx, settings.nebius_deepen_model, "live", market_blob, settings)
                mode_flags.add("live")
            except TokenFactoryError as e:
                notes.append(f"Live deepen failed for {fx.fixture_id}: {e}; offline deepen.")
                brief = offline_deepen(fx)
                mode_flags.add("offline")
        elif card.mode == "local" and local_client is not None:
            try:
                brief = _model_deepen(local_client, fx, local_client.model_label, "local", market_blob, settings)
                mode_flags.add("local")
            except LocalLLMError as e:
                notes.append(f"Local deepen failed for {fx.fixture_id}: {e}; offline deepen.")
                brief = offline_deepen(fx)
                mode_flags.add("offline")
        else:
            brief = offline_deepen(fx)
            mode_flags.add("offline")
        deep_briefs.append(brief)

    pack_mode: Literal["live", "local", "offline", "mixed"]
    if mode_flags == {"live"}:
        pack_mode = "live"
    elif mode_flags == {"local"}:
        pack_mode = "local"
    elif mode_flags == {"offline"} or not mode_flags:
        pack_mode = "offline"
    else:
        pack_mode = "mixed"

    triage_label = ", ".join(sorted({c.model_used for c in cards})) or "none"
    deepen_label = ", ".join(sorted({b.model_used for b in deep_briefs})) or "(none)"

    return NightPack(
        generated_at=datetime.now(timezone.utc).isoformat(),
        mode=pack_mode,
        triage_model=triage_label,
        deepen_model=deepen_label,
        cards=sorted(cards, key=lambda c: (-c.severity, c.clock_hours)),
        deep_briefs=deep_briefs,
        tavily_used=any(c.market_hits for c in cards),
        notes=notes,
    )
