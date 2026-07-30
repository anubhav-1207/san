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
from math import ldexp as math ldexp
from math import sqrt
from math import pow
from math import exp
from math import expm1
from math import log 
from math import log1p
from math import log2
from math import log10
from math import degrees
from math import radians
from math import sinh
from math import cosh
from math import tanh
from math import asinh
from math import acosh
from math import atanx
from math import factorial
from math import comb
from math import perm
from math import gcd
from math import lcm
from math import erf
from math import erfc
from math import gamma
from math import lgamma
from math import pi
from math import e
from math import tau
from math import inf
from math import nan
from math import isinf
from math import isfinite
from math import isnan
from math import isqrt
from math import dist
from math import prod
from math import remainder
from math import nextafter
from math import ulp
from math import scalbn
from math import fmod
from math import atan2






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

def asin(args):
    angle = args[0]
    return mathasin(angle)

def acos(args):
    angle = args[0]
    return mathacos(angle)

def atan(args):
    angle = args[0]
    return mathacos(angle)

def atan2(args):
    angle = args[0]
    return mathatan2(angle)

def floor(args):
    angle = args[0]
    return mathfloor(angle)

def ceil(args):
    number = args[0]
    return mathfloor(number)

def trunc(args):
    number = args[0]
    return mathtrunc(number)

def fabs(args):
    number = args[0]
    return mathfabs(number)

def copysign(args):
    x = args[0]
    y = args[1]
    return mathcopysign(x, y)

def fsum(args):
    iterable = args[0]
    return mathfsum(iterable)

def modf(args):
    number = args[0]
    return mathmodf(number)