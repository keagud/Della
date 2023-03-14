import re
from typing import Iterable

from prompt_toolkit.completion import (
    CompleteEvent,
    Completer,
    Completion,
    DummyCompleter,
)
from prompt_toolkit.document import Document

from .task import Task

task_path_pattern = re.compile(r"#[^\s]*$")


class TaskCompleter(Completer):
    def __init__(self, complete_base: Task) -> None:
        super().__init__()

        self.dummy = DummyCompleter()
        self.complete_base: Task = complete_base

    def dummy_complete(self, *args, **kwargs):
        return self.dummy.get_completions(*args, **kwargs)

    def get_completions(
        self, document: Document, complete_event: CompleteEvent
    ) -> Iterable[Completion]:
        if not self.complete_base.subtasks:
            return self.dummy_complete(document, complete_event)

        if not re.search(task_path_pattern, document.text_before_cursor):
            return self.dummy_complete(document, complete_event)
        return (Completion(t.slug) for t in self.complete_base.subtasks)
