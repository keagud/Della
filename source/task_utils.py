from io import FileIO
from sys import unraisablehook
from typing import Any
import json, datetime
from datetime import date
import dateparse
import toml

import re
from dateparse import Date_Formats


# TODO
# allow user to choose format for task due dates (ISO, ANSI etc)


class Task:
    def __init__(
        self,
        content: str = "",
        due_date: date | str | None = None,
        repeat: int | str = 0,
    ) -> None:
        self.content: str = content

        self.due_date: date | None = (
            due_date
            if isinstance(due_date, date) or due_date is None
            else date.fromisoformat(due_date)
        )

        self.repeat: int = int(repeat)

    def to_dict(self) -> dict:
        return {
            "content": self.content,
            "due_date": "" if self.due_date is None else self.due_date.isoformat(),
            "repeat": str(self.repeat),
        }

    def load_from_dict(self, kwargs) -> None:
        self.__init__(**kwargs)

    def __str__(self) -> str:
        formatted_task = "{} {}".format(
            self.content, "| " + self.due_date.isoformat() if self.due_date else ""
        )

        repeat_str = (
            "\n\tRepeats every {} days".format(self.repeat) if self.repeat != 0 else ""
        )

        return "".join((formatted_task, repeat_str))


#################################################################################


class Project:
    def __init__(self, name: str, project_id: str):

        self.name = name
        self.project_id = project_id
        self.tasks: list[Task] = []

    def to_dict(self) -> dict:
        return {
            "name": self.name,
            "project_id": self.project_id,
            "tasks": [t.to_dict() for t in self.tasks],
        }

    def load_from_dict(self, d: dict):

        self.__init__(name=d["name"], project_id=d["project_id"])
        self.tasks = [t.load_from_dict() for t in d["tasks"]]

    def new_task(
        self,
        task_content: str,
        task_due: date | str | None = None,
        repeat: int | str = 0,
    ):

        self.tasks.append(Task(task_content, task_due, repeat))

    # TODO why does this not print
    def print_tasks(self):
        for i, task in enumerate(self.tasks):
            print("{}.\t{}".format(i, str(task)))

    # One indexed!
    def get_task_from_number(self, selected: int) -> Task:

        if not 0 < selected < len(self.tasks) + 1:
            raise IndexError

        return self.tasks[selected - 1]


###########################################################################
class Planner:
    def load_from_dict(self, d: dict) -> None:
        self.owner_id = d["owner_id"]
        self.projects: dict[str, Project] = {
            p["name"]: Project(name=p["name"], project_id=p["project_id"])
            for p in d["projects"]
        }

    def load_from_file(self, filename: str) -> None:

        valid_extensions = [".toml", ".json"]

        if (
            not (file_extension_match := re.search(r"\..*?$", filename))
            or file_extension_match[0] not in valid_extensions
        ):
            raise FileNotFoundError(
                "Unknown file extension for file '{}'\n Valid exensions are: {}".format(
                    filename, ", ".join(valid_extensions)
                )
            )

        file_extension = file_extension_match[0]
        with open(filename, "r") as input_file:

            match (file_extension):
                case ".toml":
                    parsed_file = toml.load(input_file)
                case ".json":
                    parsed_file = json.load(input_file)

                case _:
                    raise IndexError("Unhandled filetype: '{}'".format(file_extension))

        self.load_from_dict(parsed_file)

    def __init__(self, owner_id: str = "", file: str | None = None):

        if file is not None:
            self.load_from_file(file)

        else:
            self.owner_id: str = owner_id

    def to_dict(self) -> dict:
        return {
            "owner_id": self.owner_id,
            "projects": [p.to_dict() for p in self.projects.values()],
        }

    def save_to_json(self, filename: str) -> None:
        with open(filename, "w") as output_file:
            json.dump(self.to_dict(), output_file, indent=4)

    def new_project(self, project_name: str, project_id: str) -> None:
        self.projects[project_id] = Project(project_name, project_id)


