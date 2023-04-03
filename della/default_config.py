DEFAULT_CONFIG_TEXT = r"""
# DEFAULT CONFIG FILE FOR DELLA
# Changes here are persistant: edit away!

# the message shown on prompt startup
# supports formatting with prompt_toolkit html styling
# e.g. <blue> blue text </blue>
# can also be removed altogether
start_message = "Type <ansiblue>@help</ansiblue> to see the command list"

# local options are defined here
# task_file_local determines where the task file
# is saved on this machine
[local]
task_file_local = "~/.local/della/tasks.toml"

# remote settings
# these allow you to connect to a remote server
# via ssh
[remote]
# enable or disable remote sync
use_remote = false

#ip of the server to sync with
# address = "555.555.555.555"

# location on the remote to look for a sync file
# or create, if none exists
# task_file_remote = "~/della/tasks.toml" 

#username for server login
# user = "myusername"

# location (on the local machine) to get the ssh key
# private_key_location = "~/.ssh/della"

#edit the appearance of the prompt
# styling options are: fg for forground color, bg for background
# extra for bold, italic, underline, etc

[style]
# styling to use when listing tasks
# this list is checked in order
# so the first style is for top-level tasks, the second
# is for its subtasks, etc
[[style.tasks_display]]
fg = "cyan"

[[style.tasks_display]]
fg = "green"

[[style.tasks_display]]
fg = "white"

[style.normal]
fg = "white"

# style for warning and info messages
[style.alert]
fg = "red"
extra = "bold"

# style for highlighting a command while typing
[style.highlight_command]
fg = "blue"
extra = "italic"

# style for highlighting a date while typing
[style.highlight_date]
fg = "white"
bg = "blue"
extra = "italic"

#style for highlighting a task while typing
[style.highlight_task]
fg = "yellow"
extra = "bold"

#style for the header text of the choose prompt dialog
[style.choose_title]
fg = "blue"

#style for the currently selected option of the choose prompt dialog
[style.choose_selected]
fg = "green"
extra = "italic underline"

# style for the unselected options of the choose prompt dialog
[style.choose_unselected]
fg = "cyan"
"""
