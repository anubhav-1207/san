#include "registry.h"

#include "../error.h"
#include "../interpreter.h"

#include <math.h>
#include <string.h>

#ifndef M_PI
#define M_PI 3.14159265358979323846
#endif
#ifndef M_E
#define M_E 2.71828182845904523536
#endif

static double num(Interpreter *interpreter, const Value *value) {
    if (value->type == VAL_BOOL) return value->as.bool_value ? 1.0 : 0.0;
    if (value->type == VAL_INT) return (double)value->as.int_value;
    if (value->type == VAL_FLOAT) return value->as.float_value;
    runtime_error(interpreter, ERR_INTRPTR006, 0, 0, "math functions expect numeric arguments");
    return 0.0;
}

static void domain_error(Interpreter *interpreter, const char *name) {
    runtime_error(interpreter, ERR_INTRPTR006, 0, 0, "%s() received an argument outside its domain", name);
}

#define UNARY_FLOAT(name, expression, domain_check)                                    \
    static Value fn_##name(Interpreter *interpreter, Value *args, size_t argc) {        \
        (void)argc;                                                                    \
        double x = num(interpreter, &args[0]);                                         \
        if (interpreter->halted) return value_null();                                  \
        if (domain_check) { domain_error(interpreter, #name); return value_null(); }    \
        return value_float(expression);                                                \
    }

UNARY_FLOAT(sin, sin(x), false)
UNARY_FLOAT(cos, cos(x), false)
UNARY_FLOAT(tan, tan(x), false)
UNARY_FLOAT(asin, asin(x), x < -1.0 || x > 1.0)
UNARY_FLOAT(acos, acos(x), x < -1.0 || x > 1.0)
UNARY_FLOAT(atan, atan(x), false)
UNARY_FLOAT(fabs, fabs(x), false)
UNARY_FLOAT(sqrt, sqrt(x), x < 0.0)
UNARY_FLOAT(exp, exp(x), false)
UNARY_FLOAT(log, log(x), x <= 0.0)
UNARY_FLOAT(sinh, sinh(x), false)
UNARY_FLOAT(cosh, cosh(x), false)
UNARY_FLOAT(tanh, tanh(x), false)
UNARY_FLOAT(asinh, asinh(x), false)
UNARY_FLOAT(acosh, acosh(x), x < 1.0)
UNARY_FLOAT(atanh, atanh(x), x <= -1.0 || x >= 1.0)
static Value fn_degrees(Interpreter *interpreter, Value *args, size_t argc) {
    (void)argc;
    double x = num(interpreter, &args[0]);
    if (interpreter->halted) return value_null();
    return value_float(x * 180.0 / M_PI);
}

static Value fn_radians(Interpreter *interpreter, Value *args, size_t argc) {
    (void)argc;
    double x = num(interpreter, &args[0]);
    if (interpreter->halted) return value_null();
    return value_float(x * M_PI / 180.0);
}

static Value fn_floor(Interpreter *interpreter, Value *args, size_t argc) {
    (void)argc;
    double x = num(interpreter, &args[0]);
    if (interpreter->halted) return value_null();
    return value_int((int64_t)floor(x));
}

static Value fn_ceil(Interpreter *interpreter, Value *args, size_t argc) {
    (void)argc;
    double x = num(interpreter, &args[0]);
    if (interpreter->halted) return value_null();
    return value_int((int64_t)ceil(x));
}

static Value fn_trunc(Interpreter *interpreter, Value *args, size_t argc) {
    (void)argc;
    double x = num(interpreter, &args[0]);
    if (interpreter->halted) return value_null();
    return value_int((int64_t)trunc(x));
}

static Value fn_atan2(Interpreter *interpreter, Value *args, size_t argc) {
    (void)argc;
    double y = num(interpreter, &args[0]);
    double x = num(interpreter, &args[1]);
    if (interpreter->halted) return value_null();
    return value_float(atan2(y, x));
}

static Value fn_copysign(Interpreter *interpreter, Value *args, size_t argc) {
    (void)argc;
    double x = num(interpreter, &args[0]);
    double y = num(interpreter, &args[1]);
    if (interpreter->halted) return value_null();
    return value_float(copysign(x, y));
}

static Value fn_power(Interpreter *interpreter, Value *args, size_t argc) {
    (void)argc;
    double x = num(interpreter, &args[0]);
    double y = num(interpreter, &args[1]);
    if (interpreter->halted) return value_null();
    return value_float(pow(x, y));
}

static Value fn_remainder(Interpreter *interpreter, Value *args, size_t argc) {
    (void)argc;
    double x = num(interpreter, &args[0]);
    double y = num(interpreter, &args[1]);
    if (interpreter->halted) return value_null();
    if (y == 0.0) {
        domain_error(interpreter, "remainder");
        return value_null();
    }
    return value_float(remainder(x, y));
}

static Value fn_ldexp(Interpreter *interpreter, Value *args, size_t argc) {
    (void)argc;
    double x = num(interpreter, &args[0]);
    double e = num(interpreter, &args[1]);
    if (interpreter->halted) return value_null();
    return value_float(ldexp(x, (int)e));
}

static Value fn_factorial(Interpreter *interpreter, Value *args, size_t argc) {
    (void)argc;
    double x = num(interpreter, &args[0]);
    if (interpreter->halted) return value_null();
    if (x < 0.0 || x != floor(x)) {
        domain_error(interpreter, "factorial");
        return value_null();
    }
    int64_t result = 1;
    for (int64_t i = 2; i <= (int64_t)x; i++) result *= i;
    return value_int(result);
}

static Value fn_isqrt(Interpreter *interpreter, Value *args, size_t argc) {
    (void)argc;
    double x = num(interpreter, &args[0]);
    if (interpreter->halted) return value_null();
    if (x < 0.0) {
        domain_error(interpreter, "isqrt");
        return value_null();
    }
    return value_int((int64_t)sqrt(x));
}

static Value fn_fsum(Interpreter *interpreter, Value *args, size_t argc) {
    (void)argc;
    if (args[0].type != VAL_ARRAY) {
        runtime_error(interpreter, ERR_INTRPTR006, 0, 0, "fsum() expects an array");
        return value_null();
    }
    double sum = 0.0;
    for (size_t i = 0; i < args[0].as.array->count; i++) {
        sum += num(interpreter, &args[0].as.array->items[i]);
        if (interpreter->halted) return value_null();
    }
    return value_float(sum);
}

static Value fn_prod(Interpreter *interpreter, Value *args, size_t argc) {
    (void)argc;
    if (args[0].type != VAL_ARRAY) {
        runtime_error(interpreter, ERR_INTRPTR006, 0, 0, "prod() expects an array");
        return value_null();
    }
    bool all_ints = true;
    for (size_t i = 0; i < args[0].as.array->count; i++) {
        ValueType type = args[0].as.array->items[i].type;
        if (type != VAL_INT && type != VAL_BOOL) all_ints = false;
        num(interpreter, &args[0].as.array->items[i]);
    }
    if (interpreter->halted) return value_null();
    if (all_ints) {
        int64_t product = 1;
        for (size_t i = 0; i < args[0].as.array->count; i++) {
            Value *item = &args[0].as.array->items[i];
            product *= item->type == VAL_BOOL ? (item->as.bool_value ? 1 : 0) : item->as.int_value;
        }
        return value_int(product);
    }
    double product = 1.0;
    for (size_t i = 0; i < args[0].as.array->count; i++) {
        product *= num(interpreter, &args[0].as.array->items[i]);
    }
    return value_float(product);
}

static Value fn_modf(Interpreter *interpreter, Value *args, size_t argc) {
    (void)argc;
    double x = num(interpreter, &args[0]);
    if (interpreter->halted) return value_null();
    double integer = 0.0;
    double fraction = modf(x, &integer);
    Value items[2] = {value_float(fraction), value_float(integer)};
    Value result = value_tuple(items, 2);
    value_release(&items[0]);
    value_release(&items[1]);
    return result;
}

static Value fn_frexp(Interpreter *interpreter, Value *args, size_t argc) {
    (void)argc;
    double x = num(interpreter, &args[0]);
    if (interpreter->halted) return value_null();
    int exponent = 0;
    double mantissa = frexp(x, &exponent);
    Value items[2] = {value_float(mantissa), value_int(exponent)};
    Value result = value_tuple(items, 2);
    value_release(&items[0]);
    value_release(&items[1]);
    return result;
}

static Value fn_dist(Interpreter *interpreter, Value *args, size_t argc) {
    (void)argc;
    if (args[0].type != VAL_ARRAY || args[1].type != VAL_ARRAY ||
        args[0].as.array->count != args[1].as.array->count) {
        runtime_error(interpreter, ERR_INTRPTR006, 0, 0, "dist() expects two equal-sized arrays");
        return value_null();
    }
    double total = 0.0;
    for (size_t i = 0; i < args[0].as.array->count; i++) {
        double difference = num(interpreter, &args[0].as.array->items[i]) -
                            num(interpreter, &args[1].as.array->items[i]);
        total += difference * difference;
        if (interpreter->halted) return value_null();
    }
    return value_float(sqrt(total));
}

#define CONSTANT_FN(name, expression)                                              \
    static Value fn_##name(Interpreter *interpreter, Value *args, size_t argc) {    \
        (void)interpreter; (void)args; (void)argc;                                 \
        return value_float(expression);                                            \
    }

CONSTANT_FN(pi, M_PI)
CONSTANT_FN(e, M_E)
CONSTANT_FN(inf, INFINITY)
CONSTANT_FN(nan, NAN)

static const unsigned ARITY_ZERO[] = {0};
static const unsigned ARITY_ONE[] = {1};
static const unsigned ARITY_TWO[] = {2};

const NativeEntry math_entries[] = {
    {"sin", ARITY_ONE, 1, fn_sin, "math"},
    {"cos", ARITY_ONE, 1, fn_cos, "math"},
    {"tan", ARITY_ONE, 1, fn_tan, "math"},
    {"asin", ARITY_ONE, 1, fn_asin, "math"},
    {"acos", ARITY_ONE, 1, fn_acos, "math"},
    {"atan", ARITY_ONE, 1, fn_atan, "math"},
    {"atan2", ARITY_TWO, 1, fn_atan2, "math"},
    {"floor", ARITY_ONE, 1, fn_floor, "math"},
    {"ceil", ARITY_ONE, 1, fn_ceil, "math"},
    {"trunc", ARITY_ONE, 1, fn_trunc, "math"},
    {"fabs", ARITY_ONE, 1, fn_fabs, "math"},
    {"copysign", ARITY_TWO, 1, fn_copysign, "math"},
    {"fsum", ARITY_ONE, 1, fn_fsum, "math"},
    {"modf", ARITY_ONE, 1, fn_modf, "math"},
    {"frexp", ARITY_ONE, 1, fn_frexp, "math"},
    {"ldexp", ARITY_TWO, 1, fn_ldexp, "math"},
    {"sqrt", ARITY_ONE, 1, fn_sqrt, "math"},
    {"power", ARITY_TWO, 1, fn_power, "math"},
    {"exp", ARITY_ONE, 1, fn_exp, "math"},
    {"log", ARITY_ONE, 1, fn_log, "math"},
    {"degrees", ARITY_ONE, 1, fn_degrees, "math"},
    {"radians", ARITY_ONE, 1, fn_radians, "math"},
    {"sinh", ARITY_ONE, 1, fn_sinh, "math"},
    {"cosh", ARITY_ONE, 1, fn_cosh, "math"},
    {"tanh", ARITY_ONE, 1, fn_tanh, "math"},
    {"asinh", ARITY_ONE, 1, fn_asinh, "math"},
    {"acosh", ARITY_ONE, 1, fn_acosh, "math"},
    {"atanh", ARITY_ONE, 1, fn_atanh, "math"},
    {"factorial", ARITY_ONE, 1, fn_factorial, "math"},
    {"isqrt", ARITY_ONE, 1, fn_isqrt, "math"},
    {"dist", ARITY_TWO, 1, fn_dist, "math"},
    {"prod", ARITY_ONE, 1, fn_prod, "math"},
    {"remainder", ARITY_TWO, 1, fn_remainder, "math"},
    {"pi", ARITY_ZERO, 1, fn_pi, "math"},
    {"e", ARITY_ZERO, 1, fn_e, "math"},
    {"inf", ARITY_ZERO, 1, fn_inf, "math"},
    {"nan", ARITY_ZERO, 1, fn_nan, "math"}
};

const size_t math_entry_count = sizeof(math_entries) / sizeof(math_entries[0]);
