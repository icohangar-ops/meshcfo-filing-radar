"""Deterministic offline triage/deepen.

Used when MESHCFO_INFERENCE=offline, and as the per-card fallback when
the local model (or the opt-in live client) fails on a fixture. Pure
rules over the fixture's structured_facts — no model, no network.
"""

from __future__ import annotations

from meshcfo_filing_radar.schemas import DeepBrief, SignalFixture, TriageCard


def offline_triage(fixture: SignalFixture) -> TriageCard:
    kind = fixture.signal_kind
    if kind == "both" or "4.02" in str(fixture.structured_facts):
        severity = 9
        clock = 72
        seat = "Controller (R) / CFO (A)"
        headline = f"{fixture.company.ticker}: non-reliance clock — triage CRITICAL"
        why = (
            "DEMO Item 4.02 non-reliance plus MW signal. Amendment / certification clock "
            "is active; Audit Committee will ask ownership and evidence first."
        )
    elif kind == "restatement" or "restatement" in kind:
        severity = 8
        clock = 96
        seat = "Controller"
        headline = f"{fixture.company.ticker}: restatement signal — high"
        why = "DEMO restatement path; close calendar and disclosure controls under pressure."
    else:
        severity = 6
        clock = 168
        seat = "SOX PMO"
        headline = f"{fixture.company.ticker}: MW / ICFR signal — elevated"
        why = "DEMO material-weakness disclosure; remediation testing plan needed."

    return TriageCard(
        fixture_id=fixture.fixture_id,
        company=fixture.company.display_name,
        ticker=fixture.company.ticker,
        signal_kind=fixture.signal_kind,
        filed_on=fixture.filed_on,
        severity=severity,
        clock_hours=clock,
        owner_seat=seat,
        triage_headline=headline,
        why_triage=why,
        deepen_recommended=severity >= 7,
        model_used="offline-deterministic-triage",
        mode="offline",
    )


def offline_deepen(fixture: SignalFixture) -> DeepBrief:
    facts = fixture.structured_facts
    topic = facts.get("accounting_topic") or facts.get("mw_area") or "ICFR control gap"
    return DeepBrief(
        fixture_id=fixture.fixture_id,
        ac_one_liner=(
            f"DEMO: {fixture.company.display_name} needs a named Controller-owned remediation "
            f"plan for {topic} before the next periodic report."
        ),
        why_now=facts.get("why_now")
        or facts.get("item_402")
        or "DEMO filing started an amendment / certification clock.",
        icfr_focus=[
            f"Design vs operating: {topic}",
            "Evidence: journals, hold criteria docs, recertification file",
            "COSO: Control Activities + Monitoring",
        ],
        next_actions=[
            "Controller: inventory affected periods and bill-and-hold / process population (DEMO)",
            "Process owner: attach evidence pack to each open control gap",
            "IA: schedule interim remediation test before next filing",
            "CFO: brief Audit Committee with RACI + clock",
        ],
        provenance_note=(
            "Offline deepen uses DEMO fixture structured_facts + MeshCFO playbook vocabulary. "
            "Default mode replaces this narrative with the local open-weight model; "
            "the opt-in live mode uses NVIDIA Nemotron Lightning on Nebius Token Factory."
        ),
        model_used="offline-deterministic-deepen",
        mode="offline",
    )
