import della

t = della.Task("Task content", None)
p = della.Project("id", "Project Name")
p.tasks.append(t)

with open("out.json","w") as outfile:
    outfile.write(p.to_json())

