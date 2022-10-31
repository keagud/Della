#!/usr/bin/python3

import dateparse
from datetime import date as Date
from datetime import datetime
from della import *

p = Project("PID", "A test project")
taskdate = datetime.strptime("2022-09-11", '%Y-%m-%d')
t = Task("A task", taskdate)

z = Task("Another task!", None)

p.add_task(z)


p.tasks.append(t)

with open("out.json", "w") as outfile:
    s = p.to_json()
    outfile.write(s)











