import re
from datetime import date as Date
from datetime import timedelta as Timedelta

# DEFINING CONSTANTS

Date_Formats = {"ISO":"%Y-%m-%d"}

months_short = [
    "",
    "jan",
    "feb",
    "mar",
    "apr",
    "may",
    "jun",
    "jul",
    "aug",
    "sep",
    "oct",
    "nov",
    "dec",
]  # one-indexed so that numeric month value is the same as the index

weekdays_short = [
    "",
    "mon",
    "tue",
    "wed",
    "thu",
    "fri",
    "sat",
    "sun",
]  # one-indexed for symmetry with months_short[] mostly


special_dates = {
    "christmas": "dec 25",
    "new years": "jan 1",
    "halloween": "oct 31",
}  # TODO allow user to add to this
# also TODO let this be used in the parser- currently it does not

time_intervals = ["day", "week", "month", "year"]

negative_interval_words = ["before"]
positive_interval_words = ["from", "after"]

number_words = [
    "",
    "one",
    "two",
    "three",
    "four",
    "five",
    "six",
    "seven",
    "eight",
    "nine",
    "ten",
]


# converts a list to a regex block matching any element in the list
# ex. ['a','b'] -> 'a|b'


def list_to_regex(input_list: list) -> str:
    # what if you wanted
    # to enforce static typing
    # but the python interpreter said:
    # yeah sure fuck it a string and a string[] are the same

    if len(input_list) == 1:
        return input_list[0]

    joined_str = "|".join(input_list)
    output_str = joined_str[1:] if joined_str[0] == "|" else joined_str
    return output_str


# REGEX DEFINITIONS

months_match_regex = list_to_regex(months_short)
weekday_match_regex = list_to_regex(weekdays_short)
time_interval_regex = list_to_regex(time_intervals)
number_words_regex = list_to_regex(number_words)
interval_preposition_regex = (
    list_to_regex(positive_interval_words)
    + "|"
    + list_to_regex(negative_interval_words)
)

special_dates_regex = list_to_regex(list(special_dates.keys()))


# this pattern has the following groups:
#   group 1: shortname of the month OR the month number (1-12)
#   group 2: date of the month
#   group 3 (not always present): the year in YYYY format


date_pattern = re.compile(
    r"(" + months_match_regex + r"|\d+)[^\d\n]+?(\d{1,2})([^\d\n]+\d{4})?"
)

# phrases of the form "a week from"
relative_interval_pattern = re.compile(
    r"(a\s*|"
    + number_words_regex
    + r")?\s*("
    + time_interval_regex
    + ")\w*[^\n\d\w]*("
    + interval_preposition_regex
    + ")"
)


# phrases of the form "in ten days", "in two weeks"
in_n_intervals_pattern = re.compile(
    r"in[^\n\d\w](\w+|a)[^\n\d\w](" + time_interval_regex + ")\w*?"
)

# phrases of the form "this sunday", "next wednesday"
relative_weekday_pattern = re.compile(
    r"(this|next)?[^\n\d\w]*(" + weekday_match_regex + ")"
)

special_dates_pattern = re.compile(r"(" + special_dates_regex + ")")


absolute_date_patterns = [
    date_pattern,
    in_n_intervals_pattern,
    relative_weekday_pattern,
    special_dates_pattern,
]

# removes all non-digit characters from input
def clean_whitespace(input_str: str) -> str:
    return re.sub(r"\D", "", input_str)


# calls clean_whitespace() on input str
# then casts to int before returning
def clean_and_cast(input_str: str) -> int:
    try:
        clean_str = clean_whitespace(input_str)
        return int(clean_str)
    except Exception as e:

        raise Exception("Unable to read as a number: {}".format(input_str))


def read_number(input_str: str) -> int:
    if input_str.isdigit():
        return int(input_str)

    if input_str.lower() in number_words:
        return number_words.index(input_str.lower())

    raise Exception("Tried to parse as a number and failed: {}".format(input_str))


# normalizes time interval terms to days
# "week" -> 7, etc
def normalize_interval_to_days(input_str: str) -> int:

    match input_str:
        case "day":
            days_count_multiplier = 1
        case "week":
            days_count_multiplier = 7

        case "month":
            # TODO this should take into account that months have variable number of days
            days_count_multiplier = 30
        case "year":
            # TODO same here
            # what these should both do is advance/decrement the month or year field in the final output by n
            days_count_multiplier = 365
        case _:
            raise Exception("Unknown interval type: {}".format(input_str))

    return days_count_multiplier


# takes a string of the form "<n> <days/weeks/months/years> (from)"
# returns a Timedelta object representing that amount of time


def get_interval(input_str: str) -> Timedelta:
    input_str = input_str.lower()
    interval_pattern_match = re.search(relative_interval_pattern, input_str)

    if not interval_pattern_match:
        raise LookupError("Unrecognized interval: '{}'".format(input_str))

    # unpack the matched interval phrase
    count_str, interval_type, preposition = interval_pattern_match.groups(default="one")

    days_count_multiplier = 0  # factor for converting input to a number of days
    # e.g. if the input is "week", days_count_multiplier is 7, etc

    intervals_count = 1

    if count_str in number_words:
        intervals_count = number_words.index(count_str)
    elif count_str.isdigit():
        intervals_count = int(count_str)

    days_count_multiplier = normalize_interval_to_days(interval_type)

    # a "positive" modifier means we should add the timedelta to the main date- it happens after
    # a "negative" modifier means we should subtract- it happens before
    preposition_modifier = 1 if preposition in positive_interval_words else -1

    days_delta = preposition_modifier * (days_count_multiplier * intervals_count)

    return Timedelta(days=days_delta)


# determines if input is a valid absolute date (i.e. can be translated into ISO format)
# if so, returns a match object representing it
# this is the case if the input is in one of these forms:
#   "this/next <weekday>"
#   "in <n> <days/weeks/months/years>"
#   a special predefined date (e.g. "christmas")


def get_date_match(input_str: str) -> re.Match[str]:

    matches: list[re.Match[str] | None] = [
        re.match(d, input_str) for d in absolute_date_patterns
    ]

    if not any(matches):
        raise ValueError("'{}' did not match against any known date patterns")

    return [m for m in matches if m][0]


# converts string input into a Date object
# possible inputs:
#   sept 11
#   9/11
#   9-11
#   september 11
# if a year is included, it must be last
# if no  year is included, assumed to be the next occurrence of that date


def get_absolute_date(input_str: str, allow_past_dates=True) -> Date:
    input_str = input_str.lower()

    date_match = re.search(date_pattern, input_str)

    if not date_match:

        raise Exception(
            'Unable to parse input: "{}" does not match a recognized date pattern'.format(
                input_str
            )
        )

    current_date = Date.today()

    current_year = current_date.year

    date_fields = date_match.groups(default=str(current_year))

    month_match, day_match, year_match = [item for item in date_fields]

    if month_match in months_short:
        month_match = months_short.index(month_match)
    else:
        month_match = clean_and_cast(month_match)

    day_match = clean_and_cast(day_match)
    year_match = clean_and_cast(year_match)

    # see if the date as currently calculated is in the past
    # and if that's not allowed, correct it
    date_in_past = (
        current_date.toordinal() > Date(year_match, month_match, day_match).toordinal()
    )

    if date_in_past and not allow_past_dates:
        year_match = current_year + 1

    return Date(year_match, month_match, day_match)


# takes a weekday as a string, returns the date of its next occurrence relative to today
# can also handle phrases like "this tuesday", "next tuesday"


def get_weekday_date(input_str: str, today: Date = Date.today()) -> Date:
    input_str = input_str.lower()
    weekday_match = re.search(relative_weekday_pattern, input_str)
    if not weekday_match:
        raise Exception(
            'Parse error: tried to read "{}" as a weekday name and failed'.format(
                input_str
            )
        )

    modifier, weekday = weekday_match.groups(default="this")

    weekday_index = weekdays_short.index(weekday)
    today_weekday = today.isoweekday()
    weekday_diff = weekday_index - today_weekday

    if weekday_diff < 0:
        weekday_diff = weekday_diff + 7

    if modifier == "next":
        weekday_diff = weekday_diff + 7

    return today + Timedelta(days=weekday_diff)


def get_countdown_type_date(input_str: str, today: Date = Date.today()) -> Date:

    countdown_match = re.search(in_n_intervals_pattern, input_str)

    if not countdown_match:
        raise Exception(
            'Parse error: tried to read "{}" as a "countdown interval" and failed'.format(
                input_str
            )
        )

    count, interval_type = countdown_match.groups()

    count_num = read_number(count)

    days = normalize_interval_to_days(interval_type)

    delta = Timedelta(days=(days * count_num))

    return today + delta


# general purpose function for parsing a date
# checks if the string is a match in any of the patterns in absolute_date_patterns[]
# and calls the appropriate parse function


def parse_date(
    input_str: str, allow_past_dates: bool = True, pattern: re.Pattern | None = None
) -> Date:
    input_str = input_str.lower()

    # if it's just 'today' or 'tomorrow', we don't need to go through the rest of the rigamarole
    # TODO this could prolly be refactored better

    if input_str == "today":
        return Date.today()
    elif input_str == "tomorrow":
        return Date.today() + Timedelta(days=1)

    selected_pattern = None

    if pattern:
        selected_pattern = pattern
    else:

        selected_pattern = None
        for pattern in absolute_date_patterns:
            if re.search(pattern, input_str):
                selected_pattern = pattern

    if not selected_pattern in absolute_date_patterns:
        raise Exception(
            """Parse error: "{}" does not match any known date patterns
            {} pattern was applied without success""".format(
                input_str, pattern
            )
        )

    selected_pattern_str = str(selected_pattern)

    # a learning experience for how python handles namespacing
    # we need the global keyword to access the regex patterns within the function

    global date_pattern, relative_weekday_pattern, in_n_intervals_pattern

    if selected_pattern_str == str(date_pattern):
        return get_absolute_date(input_str, allow_past_dates)
    elif selected_pattern_str == str(relative_weekday_pattern):
        return get_weekday_date(input_str)
    elif selected_pattern_str == str(in_n_intervals_pattern):
        return get_countdown_type_date(input_str)

    else:
        raise Exception(
            'Parse error: unable to apply pattern "{}" to parse string "{}"'.format(
                selected_pattern, input_str
            )
        )


# a wrapper to return a string, mostly for debugging
def parse(input_str: str) -> str:
    result = parse_date(input_str)
    return str(result)


def parse_complex_date(input_str: str, allow_past_dates=True) -> Date:

    # the "anchor date" is the absolute date to which modifiers like "before/after" are applied
    # such a date is always representable by a Date object
    anchor_date_match = get_date_match(input_str)

    if not anchor_date_match:
        raise Exception('Unable to begin parsing for "{}"'.format(input_str))

    anchor_date = parse_date(anchor_date_match.group())

    parsing_str = input_str[
        : anchor_date_match.start()
    ]  #'slice off' the bit of string with the anchor date
    date_offset = Timedelta(days=0)

    # I can't believe it's not scanf()!
    # works by parsing sucessive substrings that match relative_interval_pattern
    #   i.e. substrings of the form '<n> <time unit(s)> <before/after etc>'
    # calls get_interval to get a Timedelta, which is added to date_offset
    # when there's nothing left to parse, add date_offset to anchor_date and return it!

    while len(parsing_str) > 1:

        next_interval = get_interval(parsing_str)
        if not next_interval:
            break

        date_offset = date_offset + next_interval
        interval_match = re.search(relative_interval_pattern, parsing_str)
        parsing_str = parsing_str[: interval_match.start()]

    parsed_date = anchor_date + date_offset
    return parsed_date


# a shell for debug purposes
def shell() -> None:

    while True:
        try:

            incoming = input(">")
            if incoming.lower() == "q":
                return None

            d = get_absolute_date(incoming)
            print(str(d))
        except Exception as e:
            print(str(e))


# for testing these functions
def testing() -> None:

    dates = []
    dates.append(get_absolute_date("September 11"))
    dates.append(get_absolute_date("Oct 14, 2022"))
    dates.append(get_absolute_date("6/28/1997", False))
    dates.append(get_absolute_date("6/28/1997"))

    [print(str(d) + "!") for d in dates]
