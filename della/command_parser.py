from typing import NamedTuple, Optional

from dateparse import DateParser
from dateparse.parseutil import DateResult

from .task import TaskManager


class ParseResult(NamedTuple):
    original_input: str
    content: str
    date_result: DateResult | None = None
    parent_identifier: str | None = None


class CommandParser:
    def __init__(
        self,
        manager: Optional[TaskManager] = None,
        named_days: Optional[dict[str, str]] = None,
    ) -> None:
        if manager is not None:
            self.manager = manager
        else:
            self.manager = TaskManager()

        self.date_parser = DateParser(named_days=named_days)

    def validate_parent_id(self, parent: str):
        search_path = parent.split("/")

        for segment in search_path:
            pass

        pass

    def parse_input(self, input_str: str):
        date_match = self.date_parser.get_last(input_str)

        remainder = input_str[: date_match.start] if date_match else input_str

        remainder = remainder.strip()

        slug_patterns = [s for s in remainder.split() if s.startswith("#")]

        parent_id = None
        if slug_patterns:
            first_slug_match = slug_patterns[0]
            remainder = remainder[: remainder.index(first_slug_match)].strip()
            parent_id = first_slug_match.strip("#")

        return ParseResult(input_str, remainder, date_match, parent_id)
