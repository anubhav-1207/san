"""Native random library functions for the San runtime.

Exposes:
- random(): select a random element from an iterable
- randint(): return a random integer between start and end inclusive
- randuniform(): return a random floating-point number between start and end
"""
import random as rand


class NativeRandomFunctions:
    def __init__(self, name, expected_args, method):
        self.name = name
        self.expected_args = expected_args
        self.method = method
        self.is_native = True


def random(args):
    """Return a random element from the provided iterable."""
    return rand.choice(args[0])


def randint(args):
    """Return a random integer within the inclusive range [start, end]."""
    return rand.randint(args[0], args[1])


def randuniform(args):
    """Return a random floating-point number between start and end."""
    return rand.uniform(args[0], args[1])


def inject_random_methods(function_table):
    """Inject native random functions into the runtime function table."""
    function_table["random"] = NativeRandomFunctions("random", (1,), random)
    function_table["randint"] = NativeRandomFunctions("randint", (2,), randint)
    function_table["randuniform"] = NativeRandomFunctions("randuniform", (2,), randuniform)

######################################################################
#                           END OF FILE                              #
######################################################################
