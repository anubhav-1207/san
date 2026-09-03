#stdlib/native_builtins.py 
#-----------------------------------------------------------------------------------
# This file contains all the built-in methods

# The built-in methods are automatically loaded into the memory and importing this will
# raise error
#-----------------------------------------------------------------------------------

#---Native Function Node------------------------------------------------------------
class NativeBuiltInFunctions:
    def __init__(self,name,expected_args,method,line=None,col=None):
        self.name = name 
        self.expected_args = expected_args
        self.method = method
        self.is_native = True
        self.line = line
        self.col = col

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

def getrange(args):
    start = args[0]
    try:
        stop = args[1]
    except:
        result = []
        for i in range(start):
            result.append(i)
        return result
    
    try:
        steps = args[2]
        result = []
        for i in range(start,stop,steps):
            result.append(i)
        return result
    except:
        result = []
        for i in range(start,stop):
            result.append(i)
        return result
    
def tup(args):
    array = args[0]
    return tuple(array)

def stdout(args):
    message = args[0]
    return print(message)

#----------------------------------------------------------
def inject_builtin_methods(function_table):
    """Loads the functions into memory."""
    function_table["typeof"] = NativeBuiltInFunctions("typeof",(1,),typeof)
    function_table["setint"] = NativeBuiltInFunctions("setint",(1,),setint)
    function_table["setstr"] = NativeBuiltInFunctions("setstr",(1,),setstr)
    function_table["tup"] = NativeBuiltInFunctions("tup",(1,),tup)
    function_table["setfloat"] = NativeBuiltInFunctions("setfloat",(1,),setfloat)
    function_table["getrange"] = NativeBuiltInFunctions("getrange",(1,2,3),getrange)
    function_table["stdout"] = NativeBuiltInFunctions("stdout",(1,),stdout)
    # function_table["scank"] = NativeBuiltInFunctions("outk",(1,),scank)

#=================================================================

###########################################################################
#                           END OF FILE                                   #
###########################################################################