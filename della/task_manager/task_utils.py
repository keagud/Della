from datetime import date
import yaml, json
from inspect import getmodule

import re
import os

# TODO
# allow user to choose format for task due dates (ISO, ANSI etc)


class Task:
    def __init__(
        self,
        content: str = "",
        due_date: date | str | None = None,
        repeat: int | str = 0,
        task_dict: dict | None = None,
    ) -> None:

        if task_dict is not None:
            self.load_from_dict(task_dict)
            return

        self.content: str = content

        if due_date and due_date is not None:
            self.due_date = (
                due_date if isinstance(due_date, date) else date.fromisoformat(due_date)
            )
        else:
            self.due_date = None

        self.repeat: int = int(repeat)

    def to_dict(self) -> dict:
        return {
            "content": self.content,
            "due_date": self.due_date.isoformat()
            if isinstance(self.due_date, date)
            else "",
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
    def __init__(
        self,
        project_id: str | None,
        desc: str = "",
        project_dict: dict = {},
    ):

        self.tasks: list[Task] = []
        self.subprojects: dict[str, Project] = {}

        self.project_id = project_id
        self.desc = desc

        if project_dict.keys():
            self.load_from_dict(project_dict)
            return

    def to_dict(self) -> dict:
       return {
            "project_id": self.project_id,
            "desc": self.desc,
            "tasks": [t.to_dict() for t in self.tasks],
            "subprojects": {
                sub_id: sub_val.to_dict()
                for sub_id, sub_val in self.subprojects.items()
            },
        }

    def load_from_dict(self, d: dict):

        self.project_id = d["project_id"]
        self.desc = d["desc"]
        self.tasks = [Task(task_dict=t) for t in d["tasks"]]
        self.subprojects = {
            sub_id: Project(project_id=None, project_dict=sub_val)
            for sub_id, sub_val in d["subprojects"].items()
        }

        return self

    def new_task(
        self,
        task_content: str,
        task_due: date | str | None = None,
        repeat: int | str = 0,
    ):

        self.tasks.append(Task(task_content, task_due, repeat))

    def new_subproject(self, new_id, new_desc=""):
        self.subprojects[new_id] = Project(project_id=new_id, desc=new_desc)

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

    projects: dict[str, Project] = {}

    def __init__(self, owner_id: str = "", file: str | None = None):

        self.file = file

        if file is not None:
            self.load_from_file(file)

        else:
            self.projects = {}

        self.owner_id: str = owner_id

    def load_from_dict(self, d: dict) -> None:

        if not d.keys():
            return

        self.owner_id: str = d["owner_id"]

        projects_dict = d["projects"]

        self.projects = {
            p["project_id"]: Project(project_id=None, project_dict=p)
            for p in projects_dict.values()
        }

    def to_dict(self) -> dict:
        return {
            "owner_id": self.owner_id,
            "projects": {p: self.projects[p].to_dict() for p in self.projects},
        }

    # covers all syncing to and from the planner file
    # filename is a string specifying the file, with extension
    # action is a string specifying the type of stream- like the built-in open()
    # can be 'r' for read, or 'w' for write
    def __sync_filestream(
        self, filename: str | None = None, action: str = "r"
    ) -> dict | None:

        if (open_param := action.lower()[0]) not in ("r", "w"):
            raise KeyError("Use 'w' or 'r' to write to or read from the file")

        valid_extensions = {".yaml": getmodule(yaml), ".json": getmodule(json)}

        if filename is None:
            if (filename := self.file) is None:
                raise FileNotFoundError("No associated file for sync")

        if (
            not (file_extension_match := re.search(r"\..*?$", filename))
            or file_extension_match[0] not in valid_extensions
        ):
            raise FileNotFoundError(
                "Unknown file extension for file '{}'\n Valid exensions are: {}".format(
                    filename, ", ".join(valid_extensions.keys())
                )
            )

        file_module = valid_extensions[file_extension_match[0]]

        if file_module is None:
            raise Exception  # TODO be more specific

        with open(filename, open_param) as file_obj:
            if open_param == "r":
                in_dict = file_module.load(file_obj)
                print(in_dict)
                self.load_from_dict(in_dict)

            else:
                file_module.dump(self.to_dict(), file_obj)

    def load_from_file(self, filename=None):
        self.__sync_filestream(filename=filename, action="r")

    def write_to_file(self, filename=None):
        self.__sync_filestream(filename=filename, action="w")


    #TODO simplify the API for inherited projects
    def new_project(
        self, project_id: str, project_desc: str = "", parent: Project | None = None
    ) -> None:
        self.projects[project_id] = Project(project_id, desc=project_desc)


def make_planner(user: str | None = None, filename: str | None = None):

    user_name = os.environ["USER"] if user is None else user

    new_filename = filename if filename is not None else user_name + "_planner.toml"

    if os.path.exists(new_filename):
        raise FileExistsError("'{}' already exists".format(new_filename))

    with open(new_filename, "w") as new_file:
        new_file.write("\n")

    return Planner(owner_id=user_name, file=new_filename)


def load_planner_from_file(user: str | None = None, filename: str | None = None):

    if user is None:
        user = os.environ["USER"]

    if filename is None:
        filename = user + "_planner.yaml"

    if not os.path.exists(filename):
        raise FileNotFoundError("Cannot locate file: '{}'".format(filename))

    new_planner = Planner(file=filename)
    return new_planner
