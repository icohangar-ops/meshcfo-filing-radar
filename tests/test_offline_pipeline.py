from meshcfo_filing_radar.pipeline import run_radar


def test_offline_nightpack():
    pack = run_radar(offline=True, deep_all=True, use_tavily=False)
    assert pack.mode == "offline"
    assert len(pack.cards) == 3
    assert len(pack.deep_briefs) == 3
    assert pack.cards[0].severity >= pack.cards[-1].severity
