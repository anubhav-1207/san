#include "registry.h"

#include "../error.h"
#include "../interpreter.h"

#include <stdlib.h>

static Value native_length(Interpreter *interpreter, Value *args, size_t argc) {
    (void)argc;
    Value *value = &args[0];
    if (value->type == VAL_STR) {
        return value_int((int64_t)utf8_count(value->as.str->bytes, value->as.str->length));
    }
    if (value->type == VAL_ARRAY) return value_int((int64_t)value->as.array->count);
    if (value->type == VAL_TUPLE) return value_int((int64_t)value->as.tuple->count);
    runtime_error(interpreter, ERR_INTRPTR006, 0, 0, "len() expects a string, array or tuple");
    return value_null();
}

static bool array_index(Interpreter *interpreter, Value *array, Value *index, size_t *result) {
    if (index->type != VAL_INT && index->type != VAL_BOOL) {
        runtime_error(interpreter, ERR_INTRPTR006, 0, 0, "array index must be an integer");
        return false;
    }
    int64_t offset = index->type == VAL_BOOL ? (index->as.bool_value ? 1 : 0) : index->as.int_value;
    if (offset < 0) offset += (int64_t)array->as.array->count;
    if (offset < 0 || (size_t)offset >= array->as.array->count) {
        runtime_error(interpreter, ERR_INTRPTR006, 0, 0, "array index out of range");
        return false;
    }
    *result = (size_t)offset;
    return true;
}

static Value native_append(Interpreter *interpreter, Value *args, size_t argc) {
    (void)argc;
    Value *array = &args[0];
    if (array->type != VAL_ARRAY) {
        runtime_error(interpreter, ERR_INTRPTR006, 0, 0, "append() expects an array");
        return value_null();
    }
    ArrayObj *object = array->as.array;
    if (object->count == object->capacity) {
        size_t capacity = object->capacity * 2;
        Value *items = realloc(object->items, capacity * sizeof(*items));
        if (items == NULL) return value_null();
        object->items = items;
        object->capacity = capacity;
    }
    object->items[object->count++] = args[1];
    value_retain(&args[1]);
    return value_null();
}

static Value native_pop(Interpreter *interpreter, Value *args, size_t argc) {
    (void)argc;
    Value *array = &args[0];
    if (array->type != VAL_ARRAY) {
        runtime_error(interpreter, ERR_INTRPTR006, 0, 0, "pop() expects an array");
        return value_null();
    }
    size_t index;
    if (!array_index(interpreter, array, &args[1], &index)) return value_null();
    Value result = array->as.array->items[index];
    for (size_t i = index; i + 1 < array->as.array->count; i++) {
        array->as.array->items[i] = array->as.array->items[i + 1];
    }
    array->as.array->count--;
    return result;
}

static Value native_insert(Interpreter *interpreter, Value *args, size_t argc) {
    (void)argc;
    Value *array = &args[0];
    if (array->type != VAL_ARRAY) {
        runtime_error(interpreter, ERR_INTRPTR006, 0, 0, "insert() expects an array");
        return value_null();
    }
    if (args[1].type != VAL_INT && args[1].type != VAL_BOOL) {
        runtime_error(interpreter, ERR_INTRPTR006, 0, 0, "insert() index must be an integer");
        return value_null();
    }
    int64_t offset = args[1].type == VAL_BOOL ? (args[1].as.bool_value ? 1 : 0) : args[1].as.int_value;
    ArrayObj *object = array->as.array;
    if (offset < 0) offset += (int64_t)object->count;
    if (offset < 0) offset = 0;
    if (offset > (int64_t)object->count) offset = (int64_t)object->count;

    if (object->count == object->capacity) {
        size_t capacity = object->capacity * 2;
        Value *items = realloc(object->items, capacity * sizeof(*items));
        if (items == NULL) return value_null();
        object->items = items;
        object->capacity = capacity;
    }
    for (size_t i = object->count; i > (size_t)offset; i--) {
        object->items[i] = object->items[i - 1];
    }
    object->items[offset] = args[2];
    value_retain(&args[2]);
    object->count++;
    return value_null();
}

static Value native_del(Interpreter *interpreter, Value *args, size_t argc) {
    (void)argc;
    Value *array = &args[0];
    if (array->type != VAL_ARRAY) {
        runtime_error(interpreter, ERR_INTRPTR006, 0, 0, "del() expects an array");
        return value_null();
    }
    size_t index;
    if (!array_index(interpreter, array, &args[1], &index)) return value_null();
    value_release(&array->as.array->items[index]);
    for (size_t i = index; i + 1 < array->as.array->count; i++) {
        array->as.array->items[i] = array->as.array->items[i + 1];
    }
    array->as.array->count--;
    return value_null();
}

static const unsigned ARITY_ONE[] = {1};
static const unsigned ARITY_TWO[] = {2};
static const unsigned ARITY_THREE[] = {3};

const NativeEntry array_entries[] = {
    {"len", ARITY_ONE, 1, native_length, NULL},
    {"append", ARITY_TWO, 1, native_append, NULL},
    {"pop", ARITY_TWO, 1, native_pop, NULL},
    {"insert", ARITY_THREE, 1, native_insert, NULL},
    {"del", ARITY_TWO, 1, native_del, NULL}
};

const size_t array_entry_count = sizeof(array_entries) / sizeof(array_entries[0]);
