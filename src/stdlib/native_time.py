# stdlib/native_time.py
#---------------------------------------------------------------------------
# This file contains all the modules for the 'time' library.
# Currently, it has:
# - time()
# - sleep()
# - timezone()
#--------------------------------------------------------------------------
import time as pytime
#----------------------------------------------------------------------------
class NativeTimeFunctions:
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
def time(args):
    return pytime.time()

def timesleep(args):
    duration = args[0]
    pytime.sleep(duration)

def structime(args):
    return pytime.ctime()

#---Injector Method--------------------------------------------------------------
def inject_time_methods(function_table):
    function_table["time"] = NativeTimeFunctions("time",(0,),time)
    function_table["timesleep"] = NativeTimeFunctions("timesleep",(1,),timesleep)
    function_table["structime"] = NativeTimeFunctions("structime",(0,),structime)
#--------------------------------------------------------------------------------

########################################################################
#                           END OF FILE                                #
########################################################################