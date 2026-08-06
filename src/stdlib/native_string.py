class NativeStringFunction:
    """Wrappers for string methods.""" 
    def __init__(self,name,expected_args,method):
        self.name = name 
        self.expected_args = expected_args 
        self.method = method
        self.is_native = True

###############################################
#               Actual Functions
###############################################

#---strlen()----------------------------------
def native_length(args): #works for both string and arrays
    """Returns the length of the arguement."""
    string = args[0]
    return len(string)

#---reverse()----------------------------------------------------
def native_reverse(args):
    """Reverses the given arguement."""
    string = args[0]
    return string[::-1]

#---emptystr()------------------------------------------------------
def native_emptyString(args):
    """Returns boolean value after checking if the string is empty."""
    string = args[0]
    return string == ""

#====================================================================
def inject_string_methods(function_table):
    function_table["strlen"] = NativeStringFunction("strlen",(1,),native_length)
    function_table["reverse"] = NativeStringFunction("reverse",(1,),native_reverse)
    function_table["emptystr"] = NativeStringFunction("emptystr",(1,),native_emptyString)
#---------------------------------------------------------------------------------

###############################################################################
#                           END OF FILE                                       #
###############################################################################