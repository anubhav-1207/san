#ifndef SAN_VALUE_H
#define SAN_VALUE_H

#include "san.h"
#include "ast.h"
#include "lexer.h"

#include <stdio.h>

typedef enum {
    VAL_INT,
    VAL_FLOAT,
    VAL_BOOL,
    VAL_STR,
    VAL_ARRAY,
    VAL_TUPLE,
    VAL_NULL,
    VAL_FUNC,
    VAL_NATIVE
} ValueType;

typedef struct Value Value;
typedef struct StringObj StringObj;
typedef struct ArrayObj ArrayObj;
typedef struct TupleObj TupleObj;
typedef struct NativeEntry NativeEntry;

struct StringObj {
    size_t refcount;
    char *bytes;
    size_t length;
};

struct ArrayObj {
    size_t refcount;
    Value *items;
    size_t count;
    size_t capacity;
};

struct TupleObj {
    size_t refcount;
    Value *items;
    size_t count;
};

struct Value {
    ValueType type;
    union {
        int64_t int_value;
        double float_value;
        bool bool_value;
        StringObj *str;
        ArrayObj *array;
        TupleObj *tuple;
        const AstNode *func;
        const NativeEntry *native;
    } as;
};

Value value_int(int64_t number);
Value value_float(double number);
Value value_bool(bool boolean);
Value value_null(void);
Value value_string(const char *bytes, size_t length);
Value value_string_owned(char *bytes, size_t length);
Value value_array(size_t capacity);
Value value_tuple(const Value *items, size_t count);
Value value_func(const AstNode *node);
Value value_native(const NativeEntry *entry);

void value_retain(Value *value);
void value_release(Value *value);

bool value_truthy(const Value *value);
bool value_equal(const Value *left, const Value *right);

void value_display(FILE *stream, const Value *value);
void value_repr(FILE *stream, const Value *value);
Value value_to_string(const Value *value);

size_t utf8_count(const char *bytes, size_t length);
size_t utf8_byte_offset(const char *bytes, size_t length, size_t index);

const char *value_type_name(ValueType type);

#endif
