from math import sin as mathsin
from math import cos as mathcos
from math import tan as mathtan
from math import floor as mathfloor


class NativeFuncNode:
    def __init__(self,name,expected_args,method):
        self.name = name 
        self.expected_args = expected_args
        self.method = method
        self.is_native = True 
    
def inject_math_methods(function_table):
    function_table["sin"] = NativeFuncNode("sin",1,sin)
    function_table["cos"] = NativeFuncNode("cos",1,cos)
    function_table["tan"] = NativeFuncNode("tan",1,tan)
    function_table["floor"] = NativeFuncNode("floor",1,floor)

def sin(args):
    angle = args[0]
    return mathsin(angle)

def cos(args):
    angle = args[0]
    return mathcos(angle)

def tan(args):
    angle = args[0]
    return mathtan(angle)

def floor(args):
    number = args[0]
    return mathfloor(number)