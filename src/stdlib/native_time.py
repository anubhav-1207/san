# stdlib/native_time.py
#-----------------------------------------------------------------------------------
# Native time library bindings for SAN.

# This module exposes SAN standard library functions for time-related operations.
# The functions are injected into the SAN interpreter's function table so they
# can be called from SAN programs.

# Available native functions:
# - time(): returns the current system time in seconds since the epoch
# - timesleep(seconds): pauses execution for the requested number of seconds
# - structime(): returns a human-readable time string
#-----------------------------------------------------------------------------------
import time as pytime

class NativeTimeFunctions:
    """Wrapper class for native time functions exposed to SAN."""

    def __init__(self, name, expected_args, method):
        """Initialize a native time function binding.

        Args:
            name: function name exposed to SAN programs
            expected_args: tuple of valid argument counts
            method: callable implementing the native behavior
        """
        self.name = name
        self.expected_args = expected_args
        self.method = method
        self.is_native = True

#---Actual Methods--------------------------------------------
def time(args):
    """Return the current system time in seconds since the epoch."""
    return pytime.time()

def timesleep(args):
    """Pause execution for the supplied duration in seconds."""
    duration = args[0]
    pytime.sleep(duration)

def structime(args):
    """Return the current local time as a human-readable string."""
    return pytime.ctime()

#---Injector Method--------------------------------------------------------------
def inject_time_methods(function_table):
    """Add native time bindings to the provided function table."""
    function_table["time"] = NativeTimeFunctions("time", (0,), time)
    function_table["timesleep"] = NativeTimeFunctions("timesleep", (1,), timesleep)
    function_table["structime"] = NativeTimeFunctions("structime", (0,), structime)
#--------------------------------------------------------------------------------

########################################################################
#                           END OF FILE                                #
########################################################################