from collections import deque
from functools import reduce
from typing import Any, Callable, Iterable, Optional, cast

import dateparse
from prompt_toolkit.completion import (
    CompleteEvent,
    Completer,
    Completion,
    DummyCompleter,
)
from prompt_toolkit.document import Document
from prompt_toolkit.formatted_text import FormattedText, StyleAndTextTuples
from prompt_toolkit.layout.processors import (
    Processor,
    Transformation,
    TransformationInput,
)

from .constants import COMMAND_ALIASES
from .task import Task, TaskManager


def style_token(
    fragments: StyleAndTextTuples,
    test_func: Callable[[str], tuple[int, int] | None],
    style_apply: str,
) -> StyleAndTextTuples:
    fragments_tuples = cast(list[tuple[str, str]], fragments)

    for i, tup in enumerate(fragments_tuples):
        style, text = tup
        if (func_result := test_func(text)) is None:
            continue

        start, end = func_result

        split_fragments = [
            (style, text[:start]),
            (style_apply, text[start:end]),
            (style, text[end:]),
        ]

        fragments_tuples[i] = split_fragments[0]

        fragments_tuples.insert(i + 1, split_fragments[1])
        fragments_tuples.insert(i + 2, split_fragments[2])
        break

    return cast(StyleAndTextTuples, fragments_tuples)


class DateProcessor(Processor):
    def __init__(self, date_parser: dateparse.DateParser, *args, **kwargs) -> None:
        self.parser = date_parser
        super().__init__(*args, **kwargs)

    def find_date(self, text: str) -> tuple[int, int] | None:
        parse_result = self.parser.get_last(text)

        if parse_result is None:
            return None

        return (parse_result.start, parse_result.end)

    def apply_transformation(
        self, transformation_input: TransformationInput
    ) -> Transformation:
        fragments = style_token(transformation_input.fragments, self.find_date, "red")

        return Transformation(fragments)


class CommandProcessor(Processor):
    def __init__(self, *args, **kwargs) -> None:
        self.commands: frozenset[str] = frozenset(
            reduce(lambda s, n: s | n, COMMAND_ALIASES.values())
        )
        super().__init__(*args, **kwargs)

    def find_command(self, text: str) -> tuple[int, int] | None:
        prefix_index = text.find("@")

        if prefix_index < 0:
            return None

        command_token = text[prefix_index:].split()[0]

        if command_token.strip("@").lower() not in self.commands:
            return None

        end_index = prefix_index + len(command_token)

        return (prefix_index, end_index)

    def apply_transformation(
        self, transformation_input: TransformationInput
    ) -> Transformation:
        fragments = style_token(
            transformation_input.fragments, self.find_command, "orange"
        )

        return Transformation(fragments)


class TaskProcessor(Processor):
    def __init__(self, manager: TaskManager, *args, **kwargs) -> None:
        self.manager = manager
        super().__init__(*args, **kwargs)

    def find_task_path(self, text: str) -> tuple[int, int] | None:
        path = None

        for token in text.split():
            if token.startswith("#"):
                path = token
                break

        if path is None:
            return None

        result = self.manager.task_from_path(path)

        if result is None:
            return None

        start_index = text.index(path)
        end_index = start_index + len(path)

        return (start_index, end_index)

    def apply_transformation(
        self, transformation_input: TransformationInput
    ) -> Transformation:
        fragments = style_token(
            transformation_input.fragments, self.find_task_path, "pink"
        )

        return Transformation(fragments)


def null_complete_closure():
    null_document = Document()
    null_complete_event = CompleteEvent()
    null_completer = DummyCompleter()

    def func():
        return null_completer.get_completions(null_document, null_complete_event)

    return func


def _comp_positions(a: int | None, b: int | None):
    if a is None and b is None:
        return None

    if a is None:
        return b
    if b is None:
        return a

    return max(a, b)


def find_key_path(key_seq: list[str], input_dict: dict[str, Any]):
    """
    Given a list of task slugs as keys, and a base nested dict for completions,
    return the subdict at the end of that sequence, or None if it's invalid.

    """
    search_dict: dict | None = input_dict

    for key in key_seq[:-1]:
        if search_dict is None:
            return None

        search_dict = search_dict.get(key)

    return search_dict


def find_unique_keys(input_dict: dict[str, dict | None]):
    keys: set[str] = set(k for k, v in input_dict.items() if v is None)
    dupes = set()

    validated_input_dict: dict[str, dict] = {
        k: v for k, v in input_dict.items() if v is not None
    }

    dict_queue = deque([validated_input_dict])

    while dict_queue:
        current_dict = dict_queue.pop()

        for key in current_dict.keys():
            if key in dupes:
                continue

            if key in keys:
                keys.remove(key)
                dupes.add(key)
                continue

            keys.add(key)

        dict_queue.extendleft(d for d in current_dict.values() if d)

    return list(keys)


def find_completion_key(k: str, input_dict: dict[str, Any]):
    """
    Finds the subdict in a nested dict with the given _unique_ key, using BFS.
    If there are multiple matches or no matches, returns None.
    """
    matching: dict = {}

    dict_queue = deque([input_dict])

    while dict_queue:
        d = dict_queue.pop()

        if k in d.keys():
            if matching:
                return None

            matching = d[k]

        dict_queue.extendleft(v for v in d.values() if v)

    return None if not matching else matching


class TaskCompleter(Completer):
    def __init__(
        self,
        completions_dict: dict,
        completions_formatter: Optional[Iterable[str]] = None,
    ) -> None:
        super().__init__()
        # set by the CLI_parser when the user switches focused tasks
        # with the !set command

        self.compdict = completions_dict
        self.relative_compdict = self.compdict

        self.null_complete = null_complete_closure()()

    @classmethod
    def _dict_from_tasks(cls, task_node: Task):
        d = {}

        for task in task_node.subtasks:
            content = None

            if task.subtasks:
                content = cls._dict_from_tasks(task)

            d[task.slug] = content

        return d

    @classmethod
    def from_tasks(cls, task_root: Task):
        comp_dict = TaskCompleter._dict_from_tasks(task_root)
        return TaskCompleter(comp_dict)

    def completion_gen(
        self,
        it: Iterable[str],
        start_pos=0,
    ) -> Iterable[Completion]:
        return (
            Completion(
                txt, start_position=start_pos, display=FormattedText([("#ff0066", txt)])
            )
            for txt in it
        )

    def _keysearch(self, search_keys, search_dict=None):
        if search_dict is None:
            search_dict = self.compdict

        if not search_keys or search_keys[0] not in search_dict:
            return None

    def get_completions(self, document: Document, _) -> Iterable[Completion]:
        # avoiding regex because it scales VERY BADLY
        # and also not needed in this case
        input_tokens = document.text_before_cursor.split()
        # import ipdb; ipdb.set_trace()
        if document.char_before_cursor.isspace() or not input_tokens:
            return self.null_complete

        tail = input_tokens[-1]

        if tail.startswith("@"):
            for c in self.completion_gen(("delete", "list", "quit", "set")):
                yield c

        starts_keyword_base = tail.startswith("#")
        starts_relative_base = tail.startswith("/")

        if not (starts_relative_base or starts_keyword_base):
            return self.null_complete

        if starts_keyword_base and len(tail) == 1:
            uniques = find_unique_keys(self.compdict)

            for c in self.completion_gen(list(uniques)):
                yield c

        task_item_start = document.find_backwards("/")
        task_path_start = document.find_backwards("#")

        token_start_pos = _comp_positions(task_item_start, task_path_start)
        assert token_start_pos is not None

        path_sequence = [t.strip("#") for t in input_tokens[-1].split("/")]
        start_level: dict[str, Any] = self.compdict

        if starts_keyword_base:
            keyword_level = find_completion_key(path_sequence[0], self.compdict)
            path_sequence = path_sequence[1:]

            if not keyword_level:
                return self.null_complete

            start_level = keyword_level

        elif starts_relative_base:
            start_level = self.relative_compdict

        key_path = find_key_path(path_sequence, start_level)

        if key_path is None:
            return self.null_complete

        for match in key_path:
            yield Completion(match, start_position=token_start_pos + 1)
