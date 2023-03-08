from task import TaskManager

man = TaskManager("./test.toml")
man.add_task("a subtask")

for t in man:
    print(t)

with open("test.toml", "w") as out:
    man.serialize(out)


second = TaskManager.deserialize("test.toml")

for i in second:
    print(str(i))
