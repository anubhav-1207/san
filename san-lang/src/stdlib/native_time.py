# stdlib/native_time.py
#-----------------------------------------------------------------------------------
# Native time library bindings for San.
#
# Available:
# - time(): seconds since the epoch
# - timesleep(seconds): pause execution
# - structime(): human-readable local time
#-----------------------------------------------------------------------------------
import time as pytime


class NativeTimeFunctions:
    """Wrapper class for native time functions exposed to San."""

    def __init__(self, name, expected_args, method):
        self.name = name
        self.expected_args = expected_args
        self.method = method
        self.is_native = True


def time(args):
    """Return the current system time in seconds since the epoch."""
    return pytime.time()


def timesleep(args):
    """Pause execution for the supplied duration in seconds."""
    pytime.sleep(args[0])


def structime(args):
    """Return the current local time as a human-readable string."""
    return pytime.ctime()


def inject_time_methods(function_table):
    """Add native time bindings to the provided function table."""
    function_table["time"] = NativeTimeFunctions("time", (0,), time)
    function_table["timesleep"] = NativeTimeFunctions("timesleep", (1,), timesleep)
    function_table["structime"] = NativeTimeFunctions("structime", (0,), structime)
#--------------------------------------------------------------------------------

########################################################################
#                           END OF FILE                                #
########################################################################
