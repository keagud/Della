import sys
from collections import deque
from pprint import pprint
from typing import Any, Iterable

from prompt_toolkit import PromptSession
from prompt_toolkit.completion import (
    CompleteEvent,
    Completer,
    Completion,
    DummyCompleter,
)
from prompt_toolkit.document import Document


def find_key_path(key_seq: list[str], input_dict: dict[str, Any]):
    search_dict: dict | None = input_dict

    for key in key_seq:
        if search_dict is None:
            return None

        search_dict = search_dict.get(key)

    return search_dict


def find_completion_key(k: str, input_dict: dict[str, Any]):
    """
    Finds the subdict in a nested dict with the given _unique_ key, using BFS
    If there are multiple matches or no matches, returns None
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
    def __init__(self) -> None:
        super().__init__()

        self.compdict = {
            "a": {"rose": {"by": {"any-other-name": None, "the-sea": None}}},
            "two": {
                "birds": {
                    "in": {
                        "the": {"air": None, "street": None, "tea": None, "bush": None}
                    },
                    "with": {"one-stone": None},
                },
                "trucks": {"on-the-road": None, "having": {"tea": None, "sex": None}},
            },
        }

        # set by the CLI_parser when the user switches focused tasks
        # with the !set command
        self.relative_compdict = self.compdict

        self.dummy = DummyCompleter()
        self.nested_comps: dict | None = self.compdict

        self.leaves = ["LEAF", "END", "FINAL"]
        self.nodes = ["divorcing", "wayfarers", "alchemy"]

    def _keysearch(self, search_keys, search_dict=None):
        if search_dict is None:
            search_dict = self.compdict

        if not search_keys or search_keys[0] not in search_dict:
            return None

    def _completion_gen(self, it: Iterable[str]):
        return (Completion(txt) for txt in it)

    def get_completions(self, document: Document, complete_event: CompleteEvent):
        def no_comps():
            return self.dummy.get_completions(document, complete_event)

        if self.nested_comps is None:
            return no_comps()

        # avoiding regex because it scales VERY BADLY
        # and also not needed in this case
        input_tokens = document.text_before_cursor.split()

        if not input_tokens:
            return no_comps()

        tail = input_tokens[-1]

        starts_keyword_base = tail.startswith("#")
        starts_relative_base = tail.startswith("/")

        if not (starts_relative_base or starts_keyword_base):
            return no_comps()

        path_sequence = [t.strip("#") for t in input_tokens[-1].split("/")]

        start_level: dict[str, Any] = self.compdict

        if starts_keyword_base:
            keyword = find_completion_key(path_sequence[0], self.compdict)

            if not keyword:
                return no_comps()
            start_level = keyword

        elif starts_relative_base:
            start_level = self.relative_compdict

        return self._completion_gen(start_level.keys())


c = TestCompleter()

key_search = find_completion_key("rose", c.compdict)
assert key_search is not None
result = find_key_path("by".split(), key_search)
pprint(result)
sys.exit()

ps = PromptSession(">> ", completer=c, complete_while_typing=True)
while True:
    x = ps.prompt()
