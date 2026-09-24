"""CLI for a reproducible synthetic support implementation transaction."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

from .core import build, verify


def _read(path: Path):
    return json.loads(path.read_text(encoding="utf-8"))


def _write(path: Path, value) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def main() -> None:
    parser = argparse.ArgumentParser(description="Offline implementation transaction; synthetic reference only")
    sub = parser.add_subparsers(dest="command", required=True)
    demo = sub.add_parser("demo", help="Build the bundled synthetic support transaction")
    demo.add_argument("--output", type=Path, default=Path("generated/support-transaction.json"))
    assemble = sub.add_parser("build", help="Build a transaction from five JSON inputs")
    for name in ("spec", "proposals", "selection", "cases", "decision"):
        assemble.add_argument(name, type=Path)
    assemble.add_argument("--output", required=True, type=Path)
    check = sub.add_parser("verify", help="Recompute and validate a transaction")
    check.add_argument("package", type=Path)
    args = parser.parse_args()
    if args.command == "verify":
        verify(_read(args.package))
        print("VALID: local package recomputed; source authenticity and buyer identity not verified")
        return
    if args.command == "demo":
        examples = Path(__file__).resolve().parents[2] / "examples"
        args.spec, args.proposals, args.selection, args.cases, args.decision = (
            examples / f"{name}.json" for name in ("spec", "proposals", "selection", "cases", "decision")
        )
    package = build(*(_read(getattr(args, name)) for name in ("spec", "proposals", "selection", "cases", "decision")))
    _write(args.output, package)
    verify(_read(args.output))
    print(f"WROTE {args.output} ({package['decision']['status']}; {package['evaluation']['claim_scope']})")


if __name__ == "__main__":
    main()
