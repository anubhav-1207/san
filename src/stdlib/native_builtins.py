#stdlib/native_builtins.py 
#-----------------------------------------------------------------------------------
# This file contains all the built-in methods
# Currently, it has:
# - typeof()
# - setint()
# - setstr()
# - setfloat()

# The built-in methods are automatically loaded into the memory and importing this will
# raise error
#-----------------------------------------------------------------------------------

#---Native Function Node------------------------------------------------------------
class NativeBuiltInFunctions:
    def __init__(self,name,expected_args,method):
        self.name = name 
        self.expected_args = expected_args
        self.method = method
        self.is_native = True 

#---Type Checking--------------------------
def typeof(args):
    """Returns the type of the input."""
    ident = args[0]
    return type(ident)

#---Type Conversion -> Integer--------------------------
def setint(args):
    """Converts arguement to integer."""
    ident = args[0]
    return int(ident)

#---Type Conversion -> String----------------------------
def setstr(args):
    """Converts arguement to a string."""
    ident = args[0]
    return str(ident)

#---Type Conversion -> Float-----------------------------
def setfloat(args):
    """Converts arguement to float."""
    ident = args[0]
    return float(ident)

#----------------------------------------------------------
def inject_builtin_methods(function_table):
    """Loads the functions into memory."""
    function_table["typeof"] = NativeBuiltInFunctions("typeof",1,typeof)
    function_table["setint"] = NativeBuiltInFunctions("setint",1,setint)
    function_table["setstr"] = NativeBuiltInFunctions("setstr",1,setstr)
    function_table["setfloat"] = NativeBuiltInFunctions("setfloat",1,setfloat)
#=================================================================

###########################################################################
#                           END OF FILE                                   #
###########################################################################