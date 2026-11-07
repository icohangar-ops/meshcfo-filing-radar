"""CLI: meshcfo-radar scan | serve."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from rich.console import Console
from rich.table import Table

from meshcfo_filing_radar.pipeline import run_radar

console = Console()


def cmd_scan(args: argparse.Namespace) -> int:
    pack = run_radar(
        fixture_ids=args.fixture or None,
        offline=args.offline,
        deep_all=args.deep_all,
        use_tavily=not args.no_tavily,
        mode=args.inference,
    )
    table = Table(title="MeshCFO Filing Radar — night pack (DEMO fixtures — fictional issuers)")
    table.add_column("Sev", justify="right")
    table.add_column("Ticker")
    table.add_column("Clock h", justify="right")
    table.add_column("Owner")
    table.add_column("Headline")
    table.add_column("Mode")
    for c in pack.ranked_cards():
        table.add_row(
            str(c.severity),
            c.ticker,
            str(c.clock_hours),
            c.owner_seat[:28],
            c.triage_headline[:56],
            c.mode,
        )
    console.print(table)
    console.print(
        f"[bold]mode={pack.mode}[/] triage={pack.triage_model} deepen={pack.deepen_model} "
        f"tavily={pack.tavily_used} deep_briefs={len(pack.deep_briefs)}"
    )
    for n in pack.notes:
        console.print(f"[yellow]note:[/] {n}")

    out = Path(args.out) if args.out else None
    payload = pack.model_dump()
    if out:
        out.parent.mkdir(parents=True, exist_ok=True)
        out.write_text(json.dumps(payload, indent=2), encoding="utf-8")
        console.print(f"Wrote {out}")
    if args.json:
        print(json.dumps(payload, indent=2))
    return 0


def cmd_serve(args: argparse.Namespace) -> int:
    import uvicorn
    from meshcfo_filing_radar.api import app

    uvicorn.run(app, host=args.host, port=args.port, log_level="info")
    return 0


def main(argv: list[str] | None = None) -> None:
    parser = argparse.ArgumentParser(prog="meshcfo-radar", description="MeshCFO Filing Radar")
    sub = parser.add_subparsers(dest="cmd", required=True)

    p_scan = sub.add_parser("scan", help="Scan DEMO fixtures into a night pack")
    p_scan.add_argument("--fixture", action="append", help="Fixture id (repeatable)")
    p_scan.add_argument(
        "--inference",
        choices=["local", "live", "offline"],
        default=None,
        help="Inference engine: local (default, open-weight GGUF on this machine), "
        "offline (deterministic rules), live (Nebius Token Factory — requires "
        "MESHCFO_ENABLE_EXTERNAL=1 and a key)",
    )
    p_scan.add_argument("--offline", action="store_true", help="Force offline deterministic mode")
    p_scan.add_argument("--deep-all", action="store_true", help="Deepen every card")
    p_scan.add_argument("--no-tavily", action="store_true", help="Skip Tavily enrichment (Tavily is off by default regardless)")
    p_scan.add_argument("--out", help="Write night pack JSON path")
    p_scan.add_argument("--json", action="store_true", help="Print full JSON to stdout")
    p_scan.set_defaults(func=cmd_scan)

    p_serve = sub.add_parser("serve", help="Run local radar dashboard API")
    p_serve.add_argument("--host", default="127.0.0.1")
    p_serve.add_argument("--port", type=int, default=8765)
    p_serve.set_defaults(func=cmd_serve)

    args = parser.parse_args(argv)
    raise SystemExit(args.func(args))


if __name__ == "__main__":
    main()
