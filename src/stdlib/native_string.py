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

def native_length(args):
    string = args[0]
    return len(string)

def inject_string_methods(function_table):
    function_table["strlen"] = NativeStringFunction("strlen",1,native_length)
