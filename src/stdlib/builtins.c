#include "registry.h"

#include "../error.h"
#include "../interpreter.h"

#include <math.h>
#include <stdlib.h>
#include <string.h>

static Value native_typeof(Interpreter *interpreter, Value *args, size_t argc) {
    (void)interpreter;
    (void)argc;
    const char *name = value_type_name(args[0].type);
    return value_string(name, strlen(name));
}

static Value native_setint(Interpreter *interpreter, Value *args, size_t argc) {
    (void)argc;
    Value *value = &args[0];
    if (value->type == VAL_INT) return value_int(value->as.int_value);
    if (value->type == VAL_BOOL) return value_int(value->as.bool_value ? 1 : 0);
    if (value->type == VAL_FLOAT) return value_int((int64_t)trunc(value->as.float_value));
    if (value->type == VAL_STR) {
        char *copy = malloc(value->as.str->length + 1);
        if (copy == NULL) return value_null();
        memcpy(copy, value->as.str->bytes, value->as.str->length);
        copy[value->as.str->length] = '\0';
        char *end = NULL;
        long long parsed = strtoll(copy, &end, 10);
        if (end == copy || *end != '\0') {
            runtime_error(interpreter, ERR_INTRPTR006, 0, 0,
                          "cannot convert '%s' to int", copy);
            free(copy);
            return value_null();
        }
        free(copy);
        return value_int(parsed);
    }
    runtime_error(interpreter, ERR_INTRPTR006, 0, 0, "cannot convert value to int");
    return value_null();
}

static Value native_setfloat(Interpreter *interpreter, Value *args, size_t argc) {
    (void)argc;
    Value *value = &args[0];
    if (value->type == VAL_FLOAT) return value_float(value->as.float_value);
    if (value->type == VAL_INT) return value_float((double)value->as.int_value);
    if (value->type == VAL_BOOL) return value_float(value->as.bool_value ? 1.0 : 0.0);
    if (value->type == VAL_STR) {
        char *copy = malloc(value->as.str->length + 1);
        if (copy == NULL) return value_null();
        memcpy(copy, value->as.str->bytes, value->as.str->length);
        copy[value->as.str->length] = '\0';
        char *end = NULL;
        double parsed = strtod(copy, &end);
        if (end == copy || *end != '\0') {
            runtime_error(interpreter, ERR_INTRPTR006, 0, 0,
                          "cannot convert '%s' to float", copy);
            free(copy);
            return value_null();
        }
        free(copy);
        return value_float(parsed);
    }
    runtime_error(interpreter, ERR_INTRPTR006, 0, 0, "cannot convert value to float");
    return value_null();
}

static Value native_setstr(Interpreter *interpreter, Value *args, size_t argc) {
    (void)interpreter;
    (void)argc;
    return value_to_string(&args[0]);
}

static Value native_tup(Interpreter *interpreter, Value *args, size_t argc) {
    (void)argc;
    Value *value = &args[0];
    if (value->type != VAL_ARRAY && value->type != VAL_TUPLE) {
        runtime_error(interpreter, ERR_INTRPTR006, 0, 0, "tup() expects an array or tuple");
        return value_null();
    }
    if (value->type == VAL_TUPLE) {
        Value result = value_tuple(value->as.tuple->items, value->as.tuple->count);
        return result;
    }
    return value_tuple(value->as.array->items, value->as.array->count);
}

static Value native_getrange(Interpreter *interpreter, Value *args, size_t argc) {
    int64_t start = 0;
    int64_t stop = 0;
    int64_t step = 1;
    if (argc == 1) {
        stop = args[0].type == VAL_BOOL ? (args[0].as.bool_value ? 1 : 0) : args[0].as.int_value;
    } else {
        start = args[0].type == VAL_BOOL ? (args[0].as.bool_value ? 1 : 0) : args[0].as.int_value;
        stop = args[1].type == VAL_BOOL ? (args[1].as.bool_value ? 1 : 0) : args[1].as.int_value;
        if (argc == 3) {
            step = args[2].type == VAL_BOOL ? (args[2].as.bool_value ? 1 : 0) : args[2].as.int_value;
        }
    }
    if (step == 0) {
        runtime_error(interpreter, ERR_INTRPTR006, 0, 0, "getrange() step cannot be zero");
        return value_null();
    }
    Value array = value_array(0);
    for (int64_t i = start; (step > 0 && i < stop) || (step < 0 && i > stop); i += step) {
        if (array.as.array->count == array.as.array->capacity) {
            size_t capacity = array.as.array->capacity * 2;
            Value *items = realloc(array.as.array->items, capacity * sizeof(*items));
            if (items == NULL) break;
            array.as.array->items = items;
            array.as.array->capacity = capacity;
        }
        array.as.array->items[array.as.array->count++] = value_int(i);
    }
    return array;
}

static Value native_stdout(Interpreter *interpreter, Value *args, size_t argc) {
    (void)argc;
    value_display(interpreter->output, &args[0]);
    fputc('\n', interpreter->output);
    return value_null();
}

static const unsigned ARITY_ONE[] = {1};
static const unsigned ARITY_RANGE[] = {1, 2, 3};

const NativeEntry builtin_entries[] = {
    {"typeof", ARITY_ONE, 1, native_typeof, NULL},
    {"setint", ARITY_ONE, 1, native_setint, NULL},
    {"setstr", ARITY_ONE, 1, native_setstr, NULL},
    {"setfloat", ARITY_ONE, 1, native_setfloat, NULL},
    {"tup", ARITY_ONE, 1, native_tup, NULL},
    {"getrange", ARITY_RANGE, 3, native_getrange, NULL},
    {"stdout", ARITY_ONE, 1, native_stdout, NULL}
};

const size_t builtin_entry_count = sizeof(builtin_entries) / sizeof(builtin_entries[0]);
