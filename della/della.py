"""Console script for della."""

import argparse
import sys

from .cli import start_cli_prompt


def make_parser():
    parser = argparse.ArgumentParser()

    parser.add_argument(
        "-g",
        "--graphical",
        action="store_true",
        help="Start della in a graphical TUI window (experimental!)",
    )
    parser.add_argument(
        "command",
        nargs="*",
        help="Run a single command without opening the prompt interface",
    )

    return parser


def run():
    args = make_parser().parse_args()

    if args.graphical:
        pass

    elif args.command:
        pass

    else:
        start_cli_prompt()


if __name__ == "__main__":
    sys.exit(run())  # pragma: no cover
