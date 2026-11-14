# src/stdlib/native_math.py
#----------------------------------------------------------------------------------
# 'math' is a library wrapper for San around Python's math module.
# It is only loaded when a program runs `use math`.
#
# This vendored copy keeps the same public names as upstream San. Argument
# handling has been normalised so every function receives a plain list of args.
#----------------------------------------------------------------------------------
import math as _m


class NativeFuncNode:
    """Represent a native math function bound for the interpreter."""
    def __init__(self, name, expected_args, method):
        self.name = name
        self.expected_args = expected_args
        self.method = method
        self.is_native = True


def _unary(fn):
    def call(args):
        return fn(args[0])
    return call


def _binary(fn):
    def call(args):
        return fn(args[0], args[1])
    return call


def _zero(value):
    def call(args):
        return value
    return call


_UNARY = {
    "sin": _m.sin,
    "cos": _m.cos,
    "tan": _m.tan,
    "asin": _m.asin,
    "acos": _m.acos,
    "atan": _m.atan,
    "floor": _m.floor,
    "ceil": _m.ceil,
    "trunc": _m.trunc,
    "fabs": _m.fabs,
    "sqrt": _m.sqrt,
    "exp": _m.exp,
    "expm1": _m.expm1,
    "degrees": _m.degrees,
    "radians": _m.radians,
    "sinh": _m.sinh,
    "cosh": _m.cosh,
    "tanh": _m.tanh,
    "asinh": _m.asinh,
    "acosh": _m.acosh,
    "atanh": _m.atanh,
    "factorial": _m.factorial,
    "isqrt": _m.isqrt,
    "log": _m.log,
    "log2": _m.log2,
    "log10": _m.log10,
    "fsum": _m.fsum,
    "prod": _m.prod,
    "modf": _m.modf,
    "frexp": _m.frexp,
}

_BINARY = {
    "atan2": _m.atan2,
    "copysign": _m.copysign,
    "ldexp": _m.ldexp,
    "power": _m.pow,
    "remainder": _m.remainder,
    "dist": _m.dist,
}

_CONSTANTS = {
    "pi": _m.pi,
    "e": _m.e,
    "inf": _m.inf,
    "nan": _m.nan,
}


def inject_math_methods(function_table, modules=None):
    """Register native math functions in the interpreter's function table."""
    for name, fn in _UNARY.items():
        function_table[name] = NativeFuncNode(name, (1,), _unary(fn))
    for name, fn in _BINARY.items():
        function_table[name] = NativeFuncNode(name, (2,), _binary(fn))
    for name, value in _CONSTANTS.items():
        function_table[name] = NativeFuncNode(name, (0,), _zero(value))

#==================================================================================
###################################################################################
#                               END OF FILE                                       #
###################################################################################
