import json, datetime, re, os, argparse

from datetime import date, datetime
from datetime import date as Date

from datetime import timedelta


from task_utils import *
import dateparse


parser = argparse.ArgumentParser()
parser.add_argument('-p', '--project', help= "The project this task is attached to ")


# CONSTANT DEFINITIONS

# PROJECTS_INDEX is not a constant, but its existance is required and referenced by most of the below code
PROJECTS_INDEX = {}

# date format for changing between date objects and strings
ISO_DATE_FORMAT = r"%Y-%m-%d"


DEFAULT_FILENAME = "projects.toml"

COMMAND_KEYWORDS = ["add", "del", "ls"]

#!q -p tactile -d this saturday 


#TODO combine with dateparse

def parse_command(input_str: str):

    first_term = input_str.split(" ")[0]
    if not (first_term in COMMAND_KEYWORDS) and not first_term.startswith("/"):
        raise Exception(
            "Shell parse error: '{}' is not recognized as a command or project id".format(
                first_term
            )
        )


def shell(prompt: str = "@>"):
    #    init_projects()
    print("\t'q' to exit the shell")

    while True:

        try:
            command = input(prompt + " ")

            if command.lower() == "q":
                break

        except Exception as e:
            print(str(e))
