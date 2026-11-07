"""Pydantic models for Filing Radar night packs."""

from __future__ import annotations

from typing import Any, Literal

from pydantic import BaseModel, Field


class Excerpt(BaseModel):
    source_id: str
    form: str
    item: str
    locator: str
    filed_on: str
    excerpt: str


class Company(BaseModel):
    display_name: str
    ticker: str
    cik: str
    demo: bool = True
    industry: str = ""


class SignalFixture(BaseModel):
    fixture_id: str
    demo: bool = True
    demo_disclaimer: str = ""
    company: Company
    signal_kind: str
    forms: list[str] = Field(default_factory=list)
    filed_on: str
    period_end: str | None = None
    auditor_demo: str | None = None
    process_areas: list[str] = Field(default_factory=list)
    structured_facts: dict[str, str] = Field(default_factory=dict)
    excerpts: list[Excerpt] = Field(default_factory=list)


class MarketHit(BaseModel):
    title: str
    url: str
    snippet: str
    label: Literal["market_context"] = "market_context"
    note: str = "Tavily market/peer context — NOT EDGAR evidence"


class TriageCard(BaseModel):
    fixture_id: str
    company: str
    ticker: str
    signal_kind: str
    filed_on: str
    severity: int = Field(ge=1, le=10)
    clock_hours: int
    owner_seat: str
    triage_headline: str
    why_triage: str
    deepen_recommended: bool
    model_used: str
    mode: Literal["live", "local", "offline"]
    market_hits: list[MarketHit] = Field(default_factory=list)


class DeepBrief(BaseModel):
    fixture_id: str
    ac_one_liner: str
    why_now: str
    icfr_focus: list[str] = Field(default_factory=list)
    next_actions: list[str] = Field(default_factory=list)
    provenance_note: str
    model_used: str
    mode: Literal["live", "local", "offline"]


class NightPack(BaseModel):
    generated_at: str
    hackathon: str = "Nebius x NVIDIA Global AI Hackathon"
    product: str = "MeshCFO Filing Radar"
    brand: str = "Cubiczan"
    mode: Literal["live", "local", "offline", "mixed"]
    triage_model: str
    deepen_model: str
    cards: list[TriageCard]
    deep_briefs: list[DeepBrief] = Field(default_factory=list)
    tavily_used: bool = False
    notes: list[str] = Field(default_factory=list)

    def ranked_cards(self) -> list[TriageCard]:
        return sorted(self.cards, key=lambda c: (-c.severity, c.clock_hours))
