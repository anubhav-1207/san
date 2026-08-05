# src/stblib/native_math.py 
#----------------------------------------------------------------------------------
# 'math' is a library wrapper for San consisting of the pre-made functions in the 
# 'math' library of Python. It is not loaded into the memory automatically and is 
# only loaded when explicitly imported. 
#----------------------------------------------------------------------------------
from math import sin as mathsin
from math import cos as mathcos
from math import tan as mathtan
from math import hypot as mathhypot

from math import asin as mathasin
from math import acos as mathacos
from math import atan as mathatan
from math import atan2 as mathatan2

from math import floor as mathfloor
from math import ceil as mathceil
from math import trunc as mathtrunc
from math import fabs as mathfabs
from math import copysign as mathcopysign
from math import fsum as mathfsum
from math import modf as mathmodf
from math import frexp as mathfrexp
from math import ldexp as mathldexp
from math import sqrt as mathsqrt
from math import pow as mathpow
from math import exp as mathexp
from math import expm1 as mathexpm1

from math import degrees as mathdegrees
from math import radians as mathradians

from math import sinh as mathsinh
from math import cosh as mathcosh
from math import tanh as mathtanh
from math import asinh as mathasinh
from math import acosh as mathacosh
from math import atanh as mathatanh

from math import factorial as mathfactorial
from math import remainder as mathremainder

from math import pi as mathpi
from math import e as mathe
from math import inf as mathinf
from math import nan as mathnan

from math import isqrt as mathisqrt
from math import dist as mathdist
from math import prod as mathprod
#---------------------------------------------------------------------------------

#---Native Function Node----------------------------------------------------------
class NativeFuncNode:
    """Represent a native math function bound for the interpreter."""
    def __init__(self,name,expected_args,method):
        self.name = name 
        self.expected_args = expected_args
        self.method = method
        self.is_native = True 

#---Load functions into memory---------------------------------------------------
def inject_math_methods(function_table,modules=None):
    """Register native math functions in the interpreter's function table."""
    function_table["sin"] = NativeFuncNode("sin",1,sin)
    function_table["cos"] = NativeFuncNode("cos",1,cos)
    function_table["tan"] = NativeFuncNode("tan",1,tan)
    function_table["floor"] = NativeFuncNode("floor",1,floor)
    function_table["asin"] = NativeFuncNode("asin",1,asin)
    function_table["acos"] = NativeFuncNode("acos",1,acos)
    function_table["atan"] = NativeFuncNode("atan",1,atan)
    function_table["atan2"] = NativeFuncNode("atan2",1,atan2)
    function_table["ceil"] = NativeFuncNode("ceil",1,ceil)
    function_table["trunc"] = NativeFuncNode("trunc",1,trunc)
    function_table["fabs"] = NativeFuncNode("fabs",1,fabs)
    function_table["copysign"] = NativeFuncNode("copysign",2,copysign)
    function_table["fsum"] = NativeFuncNode("fsum",1,fsum)
    function_table["modf"] = NativeFuncNode("modf",1,modf)
    function_table["frexp"] = NativeFuncNode("frexp",1,frexp)
    function_table["ldexp"] = NativeFuncNode("ldexp",1,ldexp)
    function_table["sqrt"] = NativeFuncNode("sqrt",1,sqrt)
    function_table["power"] = NativeFuncNode("power",2,power)
    function_table["exp"] = NativeFuncNode("expm1",1,expm1)
    function_table["degrees"] = NativeFuncNode("degrees",1,degrees)
    function_table["radians"] = NativeFuncNode("radians",1,radians)
    function_table["sinh"] = NativeFuncNode("sinh",1,sinh)
    function_table["cosh"] = NativeFuncNode("cosh",1,cosh)
    function_table["tanh"] = NativeFuncNode("tanh",1,tanh)
    function_table["asinh"] = NativeFuncNode("asinh",1,asinh)
    function_table["acosh"] = NativeFuncNode("acosh",1,acosh)
    function_table["atanh"] = NativeFuncNode("atanh",1,atanh)
    function_table["factorial"] = NativeFuncNode("factorial",1,factorial)
    function_table["pi"] = NativeFuncNode("pi",0,pi)
    function_table["e"] = NativeFuncNode("e",0,e)
    function_table["inf"] = NativeFuncNode("inf",0,inf)
    function_table["isqrt"] = NativeFuncNode("isqrt",1,isqrt)
    function_table["dist"] = NativeFuncNode("dist",2,dist)
    function_table["prod"] = NativeFuncNode("prod",1,prod)
    function_table["remainder"] = NativeFuncNode("remainder",1,remainder)
    function_table["nan"] = NativeFuncNode("nan",0,nan)

#---Actual Methods---------------------------------------------------------------
def sin(args):
    """Return the sine of the first argument."""
    angle = args[0]
    return mathsin(angle)

def cos(args):
    """Return the cosine of the first argument."""
    angle = args[0]
    return mathcos(angle)

def tan(args):
    """Return the tangent of the first argument."""
    angle = args[0]
    return mathtan(angle)

def floor(args):
    """Return the floor of the first argument."""
    number = args[0]
    return mathfloor(number)

def asin(args):
    """Return the arcsine of the first argument."""
    angle = args[0]
    return mathasin(angle)

def acos(args):
    """Return the arccosine of the first argument."""
    angle = args[0]
    return mathacos(angle)

def atan(args):
    """Return the arctangent of the first argument."""
    angle = args[0]
    return mathacos(angle)

def atan2(args):
    """Return atan2 of the two arguments."""
    angle = args[0]
    return mathatan2(angle)

def ceil(args):
    """Return the ceiling of the first argument."""
    number = args[0]
    return mathfloor(number)

def trunc(args):
    """Return the truncated integer value of the first argument."""
    number = args[0]
    return mathtrunc(number)

def fabs(args):
    """Return the absolute value of the first argument."""
    number = args[0]
    return mathfabs(number)

def copysign(args):
    """Return x with the sign of y."""
    x = args[0]
    y = args[1]
    return mathcopysign(x, y)

def fsum(args):
    """Return an accurate floating-point sum of the iterable."""
    iterable = args[0]
    return mathfsum(iterable)

def modf(args):
    """Return the fractional and integer parts of the first argument."""
    number = args[0]
    return mathmodf(number)

def frexp(args):
    """Return mantissa and exponent of the first argument."""
    number = args[0]
    return mathfrexp(number)

def ldexp(args):
    """Return the first argument scaled by 2 raised to the second."""
    number = args[0]
    return mathldexp(number)

def sqrt(args):
    """Return the square root of the first argument."""
    number = args[0]
    return mathsqrt(number)

def power(args):
    """Return the first argument raised to the second power."""
    x = args[0]
    y = args[1]
    return mathpow(x,y)

def exp(args):
    """Return e raised to the power of the first argument."""
    x = args[0]
    return mathexp(x)

def expm1(args):
    """Return e**x - 1 for the first argument."""
    x = args[0]
    return mathexpm1(x)

def degrees(args):
    """Convert radians to degrees for the first argument."""
    x = args[0]
    return mathdegrees(x)

def radians(args):
    """Convert degrees to radians for the first argument."""
    x = args[0]
    return mathradians(x)

def sinh(args):
    """Return the hyperbolic sine of the first argument."""
    x = args[0]
    return mathsinh(x)

def cosh(args):
    """Return the hyperbolic cosine of the first argument."""
    x = args[0]
    return mathcosh(x)

def tanh(args):
    """Return the hyperbolic tangent of the first argument."""
    x = args[0]
    return mathtanh(x)

def asinh(args):
    """Return the inverse hyperbolic sine of the first argument."""
    x = args[0]
    return mathasinh(x)

def acosh(args):
    """Return the inverse hyperbolic cosine of the first argument."""
    x = args[0]
    return mathacosh(x)

def atanh(args):
    """Return the inverse hyperbolic tangent of the first argument."""
    x = args[0]
    return mathatanh(x)

def factorial(args):
    """Return the factorial of the first integer argument."""
    x = args[0]
    return mathfactorial(x)

def pi(args):
    """Return the constant pi."""
    return mathpi

def e(args):
    """Return the constant e."""
    return mathe

def inf(args):
    """Return positive infinity."""
    return mathinf

def isqrt(args):
    """Return the integer square root of the first argument."""
    x = args[0]
    return mathisqrt(x)

def dist(args):
    """Return the Euclidean distance between two points."""
    x = args[0]
    y = args[1]
    return mathdist(x,y)

def prod(args):
    """Return the product of values in the iterable."""
    iterable = args[0]
    return mathprod(iterable)

def remainder(args):
    """Return the IEEE 754-style remainder of x / y."""
    x = args[0]
    y = args[1]
    return mathremainder(x,y)

def nan(args):
    """Return a NaN value."""
    return mathnan
#==================================================================================
###################################################################################
#                               END OF FILE                                       #
###################################################################################