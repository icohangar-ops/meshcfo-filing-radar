"""Load DEMO filing fixtures shipped with the repo."""

from __future__ import annotations

import json
from pathlib import Path

from meshcfo_filing_radar.schemas import SignalFixture

ROOT = Path(__file__).resolve().parents[2]
FIXTURES_DIR = ROOT / "fixtures"


def list_fixture_ids() -> list[str]:
    return sorted(p.stem for p in FIXTURES_DIR.glob("*.json"))


def load_fixture(fixture_id: str) -> SignalFixture:
    path = FIXTURES_DIR / f"{fixture_id}.json"
    if not path.is_file():
        # allow short aliases matching stem
        matches = list(FIXTURES_DIR.glob(f"{fixture_id}*.json"))
        if not matches:
            raise FileNotFoundError(f"Unknown fixture: {fixture_id}")
        path = matches[0]
    data = json.loads(path.read_text(encoding="utf-8"))
    return SignalFixture.model_validate(data)


def load_all() -> list[SignalFixture]:
    return [load_fixture(i) for i in list_fixture_ids()]
