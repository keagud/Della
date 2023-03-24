import functools
from time import perf_counter


def stopwatch(func):
    """Print the time a function took to execute"""

    @functools.wraps(func)
    def wrapper_stopwatch(*args, **kwargs):
        start_time = perf_counter()
        return_val = func(*args, **kwargs)
        end_time = perf_counter()

        print(f"{func.__name__} executed in {end_time - start_time :.3} sec")

        return return_val

    return wrapper_stopwatch


def debug(func):
    """Print the function signature and return value"""

    @functools.wraps(func)
    def wrapper_debug(*args, **kwargs):
        args_repr = [repr(a) for a in args]  # 1
        kwargs_repr = [f"{k}={v!r}" for k, v in kwargs.items()]  # 2
        signature = ", ".join(args_repr + kwargs_repr)  # 3
        print(f"Calling {func.__name__}({signature})")
        value = func(*args, **kwargs)
        print(f"{func.__name__!r} returned {list(value)!r}")  # 4
        return value

    return wrapper_debug
