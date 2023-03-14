import re
from typing import Iterable

from prompt_toolkit import prompt
from prompt_toolkit.completion import CompleteEvent, Completer, Completion
from prompt_toolkit.document import Document

pat = re.compile(r"[^/\s#]+")


class TaskCompleter(Completer):
    def __init__(self) -> None:
        super().__init__()

    def get_completions(
        self, document: Document, complete_event: CompleteEvent
    ) -> Iterable[Completion]:
        input_start, input_end = document.find_boundaries_of_current_word()

        selection = document.get_word_before_cursor(pattern=pat)

        if selection.endswith("/"):
            selection = selection[:-1]

        return (Completion(selection) for c in range(10))


tc = TaskCompleter()

x = prompt(completer=tc, complete_while_typing=True)
