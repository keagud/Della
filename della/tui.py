from textual.app import App, ComposeResult
from textual.widgets import Tree
from textual.widgets.tree import TreeNode

from .task import Task, TaskManager


def make_task_tree(manager: TaskManager):
    tree: Tree[dict] = Tree("Tasks")
    tree.show_root = False

    def add_node(p: TreeNode, t: Task):
        is_not_leaf = True if t.subtasks != [] else False

        display_str = str(t)

        new_node = p.add(display_str, allow_expand=is_not_leaf)

        if is_not_leaf:
            for s in t.subtasks:
                add_node(new_node, s)

    for task in manager.root_task.subtasks:
        add_node(tree.root, task)

    return tree


def make_app(tasks: TaskManager):
    class TreeApp(App):
        def compose(self) -> ComposeResult:
            yield make_task_tree(tasks)

    return TreeApp


def main():
    t = TaskManager("test.toml")
    sub = t.add_task("do a thing")
    t.add_task("a subtask", parent=sub)
    lower = t.add_task("another subtask", parent=sub)
    t.add_task("this one is three deep", parent=lower)
    sub = t.add_task("a second first level task")
    t.add_task("subtast to the second one", parent=sub)

    app = make_app(t)()
    app.run()


if __name__ == "__main__":
    main()
