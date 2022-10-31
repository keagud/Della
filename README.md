# Della
**Della** is a CLI todo list manager/simple project organizer/general-purpose notebook utility, written in Python. Its goal is to provide a framework for keeping track of things that's broad enough to cover (nearly) anything you might write on a post-it, while keeping command syntax limited to a small and easily remembered set of keywords.


## Use and Features
Running the `della` command without arguments will open a shell prompt. When run for the first time, you will be prompted to select a storage location for associated files; the default is `~/.local/della`

Della allows the user to define *tasks* consisting of a text description and (optionally) an associated date.

`@ mow the lawn`

`@ mow the lawn this saturday`

Della is smart enough to parse simple natural language time expressions and evaluate them relative to the current date --see `dateparse.py` for these features as a standalone module.

`@ mow the lawn this saturday`

`...a week after this monday`

`...august 19`

`... ten days before a week after july 27, 2026`

 Tasks can also be grouped into *projects.* Add a project with `add <id> <name>`or just run `add` and follow the prompts.

`@ add coding Programming Projects`

Della will interpret the first word after `add` as the project id, and any remaining text will become the full name of the new project. To add tasks to the new project use /<id>:

`@ /coding make fizzbuzz in haskell this saturday`

`@ /coding grow a magnificent beard worthy of Stallman`

Then `/<id>` with no other arguments will display all the tasks in that project:
```
@ /coding
	Upcoming tasks in Programming Projects:
	1. make fizzbuzz in haskell | 9/10 (in 3 days)
	2. port Doom to vim   | 10/27 (in 1 month, 20 days)
	3. grow a magnificent beard worthy of Stallman
```
By default, tasks are shown with those due soonest first. To list tasks that are not in a project, use `ls.` `ls all` will print all tasks in all projects.

The `due` keyword can be used to list only tasks due before the specified date:

`@ ls due in two weeks`

`@ /coding due in a month`


To delete a task, use the `del` keyword, followed by the project id (if it's in a project) and the task number - this is printed next to each task when listed.
```
@ del coding 1
	deleted "make fizzbuzz in haskell"
...
@ del coding 1,3
	deleted 2 tasks: "make fizzbuzz in haskell", "port Doom to vim"
...
@ del coding 1-2
	deleted 2 tasks: "make fizzbuzz in haskell", "grow a magnificent beard
		worthy of Stallman"
```

Similarly, whole projects can be deleted with `del <id> all`. `undo` will revert the most recent deletion - but only the most recent!


## Additional technical details

All task and project data is serialized into JSON format and stored in `projects.json` at `~/.local/della` or whatever location you chose on startup.

 As an independent, modern woman, Della has no dependencies outside the Python standard library. She does however require Python 3.10 or higher. I've only personally tested this on Linux (Fedora 36 and Arch) but in theory there's nothing preventing it from running on MacOS or anything POSIX with Python 3.10. If you run MacOS please let me know if/how it works!



