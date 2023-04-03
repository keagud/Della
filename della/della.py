"""Console script for della."""

import argparse
import sys

from .cli import CLI_Parser, start_cli_prompt


def make_parser():
    parser = argparse.ArgumentParser()

    parser.add_argument(
        "command",
        nargs="?",
        type=str,
        help="Run a single command without opening the prompt interface",
        default=None,
    )

    return parser


def run():
    args = make_parser().parse_args()

    if args.command is not None:
        with CLI_Parser() as cli_parser:
            cli_parser.from_prompt(args.command)

    else:
        start_cli_prompt()


if __name__ == "__main__":
    sys.exit(run())  # pragma: no cover
