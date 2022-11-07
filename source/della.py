import json, datetime, re, os

from datetime import date, datetime
from datetime import date as Date

from datetime import timedelta


# TODO
# 	implement code to accept user input


# CONSTANT DEFINITIONS

# PROJECTS_INDEX is not a constant, but its existance is required and referenced by most of the below code
PROJECTS_INDEX = {}

# date format for changing between date objects and strings
ISO_DATE_FORMAT = r"%Y-%m-%d"


# TODO should this maybe be TOML?

DEFAULT_FILENAME = "projects.json"  # default filename for reading/writing project JSON

JSON_PATH = os.path.expanduser("~/.local/share/della")

# This is unavoidably OOP, but i think a fair use case
# the PROJECTS_INDEX dict indexes all Project objects by Project.proj_id
# in turn Project.tasks[] is a list of Task objects


class Project:
    name = ""
    proj_id = ""
    tasks = []

    # projects are added to PROJECTS_INDEX at init time
    def __init__(self, proj_id: str, name: str, tasks=[]):
        self.name = name
        self.proj_id = proj_id
        if proj_id in PROJECTS_INDEX:
            raise ValueError(
                'A project with the id "{}" already exists'.format(proj_id)
            )
        PROJECTS_INDEX[proj_id] = self

    def add_task(self, new_task):
        self.tasks.append(new_task)

    # TODO use this for user control of tasks
    # e.g. referencing tasks for deletion or changes
    def list_tasks(self):
        task_number = 1
        for task in self.tasks:
            print(str(task_number) + " " + task.display(countdown=True))
            task_number += 1

    # can delete a task by number(one-indexed position in Project.tasks[])
    # or directly by passing the Task object to be deleted

    def del_task(self, task_number: int):

        if task_number > len(self.tasks) or task_number < 1:

            raise IndexError(
                'Invalid task number "{}" - there are only "{}" tasks in the project "{}"'.format(
                    str(task_number), str(len(self.tasks)), self.name
                )
            )

        del self.tasks[task_number - 1]

    def to_json(self) -> str:

        return json.dumps(
            {
                "name": self.name,
                "id": self.proj_id,
                "tasks": [t.to_dict() for t in self.tasks],
            },
            indent=4,
        )


class Task:
    content = ""
    due_date: Date | None = None
    repeats = False
    repeat_interval = 0

    def __init__(
        self,
        content: str,
        due_date: Date | None = None,
        repeats=False,
        repeat_interval=0,
    ):
        self.content = content
        self.due_date = due_date
        self.repeats = repeats
        self.repeat_interval = repeat_interval

    def to_dict(self) -> dict:
        return {
            "content": self.content,
            "due_date": self.due_date.strftime(ISO_DATE_FORMAT)
            if self.due_date is not None
            else "",
            "repeats": self.repeats,
            "repeat_interval": self.repeat_interval,
        }

    def get_time_until(self) -> timedelta | None:

        if self.due_date is None:
            return None

        now: Date = datetime.now()
        delta = self.due_date - now
        return delta

    # TODO justify text to line up consistantly in nice columns
    def display(self, countdown: bool = False):
        display_string = "{} | {}".format(
            self.content,
            self.due_date.strftime("%a, %b %-d %y")
            if self.due_date is not None
            else "(no due date)",
        )  # "Wed, Oct 3 22"

        if countdown and self.due_date is not None:
            display_string += "in {} days".format(self.get_time_until().days)

        if self.repeats:
            display_string += "repeats every {} days".format(str(self.repeat_interval))

        return display_string


# generates a JSON formatted string of Projects indexed by id
# then writes it to output_filename
def write_projects_to_file(output_filename: str = DEFAULT_FILENAME) -> None:

    write_string = "{\n"

    for project_id in PROJECTS_INDEX:
        project_to_write = PROJECTS_INDEX[project_id]
        write_string += '"{}":'.format(project_to_write.proj_id)
        write_string += project_to_write.to_json()
        write_string += "\n"

    write_string += "\n}"

    with open(output_filename, "w") as output_file:
        output_file.write(write_string)


class Planner:

    name: str = ""
    file: str = ""
    
    projects: dict[str, Project]

    def __init__(self, name: str = "", projects_file: str = "") -> None:
        self.name = name
        self.file = projects_file





# loads the JSON in input_filename into Project objects
# which are stored in PROJECTS_INDEX and are indexed by Project.proj_id
def load_projects_from_file(
    path: str = "~/.local/della", input_filename: str = DEFAULT_FILENAME
) -> None:
    global PROJECTS_INDEX
    input_text = ""
    path = os.path.expanduser(path)

    full_path = "{}/{}".format(path, input_filename)

    assert os.path.exists(full_path)

    with open(full_path, "r") as input_file:
        input_text = input_file.read()

    if not input_text:
        return None

    loaded_projects = json.loads(input_text)
    # the loaded format is a dict with project ids as keys
    # loaded_projects['id'] -> another dict with keys corresponding to Project obj field

    for project_key in loaded_projects:
        project_dict = loaded_projects[project_key]

        if project_dict["id"] in PROJECTS_INDEX.keys():
            conflicting_project = PROJECTS_INDEX[project_dict["id"]]
            print(
                'Duplicate ID: projects "{}" and "{}" both have the ID "{} -- skipping loading for "{}"'.format(
                    project_dict["name"],
                    conflicting_project.name,
                    project_dict["id"],
                    project_dict["id"],
                )
            )
        else:

            loaded_project = Project(project_dict["id"], project_dict["name"])
            loaded_project.tasks = [
                Task(task_dict) for task_dict in project_dict["tasks"]
            ]
            PROJECTS_INDEX[loaded_project.proj_id] = loaded_project


def print_projects():
    for k in PROJECTS_INDEX:
        p = PROJECTS_INDEX[k]
        print("=== {} / {}=====\n".format(p.proj_id, p.name))
        p.list_tasks()


def init_projects(projects_filename: str = DEFAULT_FILENAME):

    global PROJECTS_INDEX

    # make the project folder if it doesn't exist
    os.makedirs(JSON_PATH, exist_ok=True)

    full_path = "{}/{}".format(JSON_PATH, projects_filename)

    # make a new JSON if one is not already present
    if not os.path.exists(full_path):
        print(
            "No existing project JSON found - making a new one at ~/.local/della/projects.json..."
        )
        new_json = open(full_path, "w")
        new_json.write("{}")
        new_json.close()

    try:
        load_projects_from_file(path=JSON_PATH, input_filename=projects_filename)
        assert PROJECTS_INDEX != None
    except (AssertionError, AttributeError):
        print("Could not validate the project file path")
        return None


COMMAND_KEYWORDS = ["add", "del", "ls"]


def parse_command(input_str: str):

    first_term = input_str.split(" ")[0]
    if not (first_term in COMMAND_KEYWORDS) and not first_term.startswith("/"):
        raise Exception(
            "Shell parse error: '{}' is not recognized as a command or project id".format(
                first_term
            )
        )


# TODO


def shell(prompt: str = "@>"):
    init_projects()
    loop = True
    print("\t'q' to exit the shell")

    while True:

        try:
            command = input(prompt + " ")

            if command.lower() == "q":
                break

        except Exception as e:
            print(str(e))
