"""Local-first defaults: local inference, external services off."""

import pytest

from meshcfo_filing_radar.config import Settings
from meshcfo_filing_radar.pipeline import run_radar


def test_defaults_are_local_first():
    s = Settings()
    assert s.inference_mode == "local"
    assert s.enable_external_services is False
    # Even the readiness gates must stay closed without the opt-in.
    assert s.live_llm_ready is False
    assert s.tavily_allowed is False


def test_keys_alone_do_not_enable_external_services():
    s = Settings(nebius_api_key="dummy", tavily_api_key="dummy")
    assert s.resolved_nebius_key() == "dummy"
    assert s.live_llm_ready is False
    assert s.tavily_allowed is False

    s2 = Settings(
        nebius_api_key="dummy", tavily_api_key="dummy", enable_external_services=True
    )
    assert s2.live_llm_ready is True
    assert s2.tavily_allowed is True


def test_offline_mode_via_settings():
    pack = run_radar(
        settings=Settings(inference_mode="offline"), deep_all=True, use_tavily=False
    )
    assert pack.mode == "offline"
    assert len(pack.cards) == 3
    assert all(c.mode == "offline" for c in pack.cards)
    assert pack.tavily_used is False


@pytest.mark.skipif(
    not Settings().local_model_file.is_file(),
    reason="local GGUF model not present on this machine",
)
def test_local_model_smoke_one_fixture():
    """End-to-end local run on one DEMO fixture (slow; needs the GGUF)."""
    pack = run_radar(
        settings=Settings(),
        fixture_ids=["northstar"],
        deep_all=True,
        use_tavily=False,
    )
    assert len(pack.cards) == 1
    card = pack.cards[0]
    # Either the local model answered, or the run honestly fell back.
    assert card.mode in {"local", "offline"}
    if card.mode == "local":
        assert card.model_used.startswith("local:")
        assert 1 <= card.severity <= 10
        assert pack.mode in {"local", "mixed"}
