"""Native random library functions for the SAN runtime.

This module defines native wrappers around Python's random library for use in
SAN programs. It exposes the following functions:
- random(): select a random element from an iterable
- randint(): return a random integer between start and end inclusive
- randuniform(): return a random floating-point number between start and end
- inject_random_methods(): register the native random functions in the runtime
"""

# stdlib/native_random.py
#---------------------------------------------------------------------------
# This file contains all the modules for the 'random' library.
# Currently, it has:
# - random()
# - randint()
# - randuniform()
# --------------------------------------------------------------------------
import random as rand
#----------------------------------------------------------------------------
class NativeRandomFunctions:
    def __init__(self,name,expected_args,method):
        """Initialize a native random function binding.

        name: the function name exposed to SAN programs
        expected_args: tuple of accepted argument counts
        method: callable implementing the native behavior
        """
        self.name = name 
        self.expected_args = expected_args
        self.method = method
        self.is_native = True 

#---Actual Methods--------------------------------------------
def random(args):
    """Return a random element from the provided iterable.
    
    args: a single-element list or tuple containing the iterable.
    """
    iterable = args[0]
    return rand.choice(iterable)

def randint(args):
    """Return a random integer within the inclusive range [start, end].
    
    args: a two-element list or tuple containing start and end values.
    """
    start = args[0]
    end = args[1]
    return rand.randint(start,end)

def randuniform(args):
    """Return a random floating-point number between start and end.
    
    args: a two-element list or tuple containing start and end values.
    """
    start = args[0]
    end = args[1]
    return rand.uniform(start,end)

def inject_random_methods(function_table):
    """Inject native random functions into the runtime function table.
    
    function_table: dictionary mapping function names to native wrappers.
    """
    function_table["random"] = NativeRandomFunctions("random",(1,),random)
    function_table["randint"] = NativeRandomFunctions("randint",(2,),randint)
    function_table["randuniform"] = NativeRandomFunctions("randuniform",(2,),randuniform)
######################################################################
#                           END OF FILE                              #
######################################################################