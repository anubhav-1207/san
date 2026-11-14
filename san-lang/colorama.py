"""Minimal local stand-in for the `colorama` package.

The San interpreter uses colorama only to colour its terminal messages. On this
machine colorama is not installed and there is no package index access, so this
shim provides the handful of names main.py imports.
"""


class Fore:
    RED = "\033[31m"
    GREEN = "\033[32m"
    YELLOW = "\033[33m"
    BLUE = "\033[34m"
    CYAN = "\033[36m"
    WHITE = "\033[37m"
    LIGHTMAGENTA_EX = "\033[95m"
    RESET = "\033[39m"


class Style:
    RESET_ALL = "\033[0m"


def init(autoreset=False):
    return None
