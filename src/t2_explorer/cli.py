"""Command-line interface: snapshot | build | all."""

import argparse
import sys

from .site import build_site
from .snapshot import SnapshotAborted, run_snapshot


def main(argv: list[str] | None = None) -> int:
    """Run the requested pipeline stage; exit 2 when a snapshot guard aborts."""
    parser = argparse.ArgumentParser(prog="t2_explorer", description=__doc__)
    parser.add_argument("command", choices=("snapshot", "build", "all"))
    args = parser.parse_args(argv)
    try:
        if args.command in ("snapshot", "all"):
            run_snapshot()
        if args.command in ("build", "all"):
            build_site()
    except SnapshotAborted as abort:
        print(f"snapshot aborted: {abort}", file=sys.stderr)
        return 2
    return 0
