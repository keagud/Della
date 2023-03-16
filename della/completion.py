from collections import deque
from typing import Any, Iterable

from prompt_toolkit import PromptSession
from prompt_toolkit.completion import (
    CompleteEvent,
    Completer,
    Completion,
    DummyCompleter,
)
from prompt_toolkit.document import Document


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
    keys: set[str] = set()
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


class TestCompleter(Completer):
    def __init__(self, completions_dict: dict) -> None:
        super().__init__()
        # set by the CLI_parser when the user switches focused tasks
        # with the !set command

        self.compdict = completions_dict
        self.relative_compdict = self.compdict

        self.null_complete = null_complete_closure()()

        self.leaves = ["LEAF", "END", "FINAL"]
        self.nodes = ["divorcing", "wayfarers", "alchemy"]

    @classmethod
    def from_nested_dict(cls, data: dict):
        pass

    def completion_gen(
        self,
        it: Iterable[str],
        start_pos=0,
    ) -> Iterable[Completion]:
        import ipdb

        ipdb.set_trace()

        for txt in it:
            yield Completion(txt, start_position=start_pos)

    def _keysearch(self, search_keys, search_dict=None):
        if search_dict is None:
            search_dict = self.compdict

        if not search_keys or search_keys[0] not in search_dict:
            return None

    def get_completions(
        self, document: Document, complete_event: CompleteEvent
    ) -> Iterable[Completion]:
        # avoiding regex because it scales VERY BADLY
        # and also not needed in this case

        input_tokens = document.text_before_cursor.split()

        if not input_tokens:
            return self.null_complete

        tail = input_tokens[-1]

        starts_keyword_base = tail.startswith("#")
        starts_relative_base = tail.startswith("/")

        if not (starts_relative_base or starts_keyword_base):
            return self.null_complete

        if starts_keyword_base and len(tail) == 1:
            import ipdb

            ipdb.set_trace()
            uniques = find_unique_keys(self.compdict)
            x = self.completion_gen(list(uniques))
            return x

        task_item_start = document.find_backwards("/")
        task_path_start = document.find_backwards("#")

        token_start_pos = _comp_positions(task_item_start, task_path_start)
        assert token_start_pos is not None

        path_sequence = [t.strip("#") for t in input_tokens[-1].split("/")]
        #        pprint (path_sequence)
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


compdict = {
    "a": {"rose": {"by": {"any-other-name": None, "the-sea": None}}},
    "two": {
        "birds": {
            "in": {"the": {"air": None, "trucks": None, "tea": None, "bush": None}},
            "with": {"one-stone": None},
        },
        "trucks": {"on-the-road": None, "having": {"tea": None, "sex": None}},
    },
}
# sys.exit()
c = TestCompleter(compdict)
ps = PromptSession(">> ", completer=c, complete_while_typing=True)
while True:
    x = ps.prompt()
