"""Optional Tavily market-context enrichment (never treated as EDGAR evidence)."""

from __future__ import annotations

import json
import urllib.request
import urllib.error
from typing import Any

from meshcfo_filing_radar.schemas import MarketHit, SignalFixture


def search_market_context(api_key: str, fixture: SignalFixture, max_results: int = 3) -> list[MarketHit]:
    topic = fixture.structured_facts.get("accounting_topic") or fixture.structured_facts.get("mw_area") or "material weakness ICFR"
    industry = fixture.company.industry or "public company"
    query = f"{topic} {industry} remediation peer practices"
    body = json.dumps(
        {
            "api_key": api_key,
            "query": query,
            "max_results": max_results,
            "search_depth": "basic",
            "include_answer": False,
        }
    ).encode("utf-8")
    req = urllib.request.Request(
        "https://api.tavily.com/search",
        data=body,
        headers={"Content-Type": "application/json"},
        method="POST",
    )
    try:
        with urllib.request.urlopen(req, timeout=30) as resp:
            data: dict[str, Any] = json.loads(resp.read().decode("utf-8"))
    except urllib.error.HTTPError as e:
        err = e.read().decode("utf-8", errors="replace")[:300]
        raise RuntimeError(f"Tavily HTTP {e.code}: {err}") from e

    hits: list[MarketHit] = []
    for item in data.get("results") or []:
        hits.append(
            MarketHit(
                title=(item.get("title") or "Untitled")[:200],
                url=item.get("url") or "",
                snippet=(item.get("content") or "")[:400],
            )
        )
    return hits
