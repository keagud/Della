import argparse
import json
from task_utils import *
import sys

commands = "ls rm add".split(" ")


main_parser = argparse.ArgumentParser()

subparser = main_parser.add_subparsers(dest="command")

subparsers = {command: subparser.add_parser(command) for command in commands}

for c, a in subparsers.items():
    a.add_argument("-p", "--project")


subparsers["add"].add_argument("name", nargs="+")
subparsers["add"].add_argument("-d", "--date")



cli_args = sys.argv[1:] if len(sys.argv) > 1 else ["ls"]

if cli_args[0] not in ("add", "ls", "rm"):
    cli_args = ["add"] + cli_args


args = main_parser.parse_args(cli_args)

print(json.dumps(vars(args)))
