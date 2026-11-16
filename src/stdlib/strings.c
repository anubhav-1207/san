#include "registry.h"

#include "../error.h"
#include "../interpreter.h"

#include <stdlib.h>
#include <string.h>

static Value native_strlen(Interpreter *interpreter, Value *args, size_t argc) {
    (void)argc;
    if (args[0].type != VAL_STR) {
        runtime_error(interpreter, ERR_INTRPTR006, 0, 0, "strlen() expects a string");
        return value_null();
    }
    return value_int((int64_t)utf8_count(args[0].as.str->bytes, args[0].as.str->length));
}

static Value native_reverse(Interpreter *interpreter, Value *args, size_t argc) {
    (void)argc;
    if (args[0].type != VAL_STR) {
        runtime_error(interpreter, ERR_INTRPTR006, 0, 0, "reverse() expects a string");
        return value_null();
    }
    StringObj *string = args[0].as.str;
    size_t count = utf8_count(string->bytes, string->length);
    size_t *offsets = malloc((count + 1) * sizeof(*offsets));
    if (offsets == NULL) return value_null();
    for (size_t i = 0; i <= count; i++) {
        offsets[i] = utf8_byte_offset(string->bytes, string->length, i);
    }
    char *bytes = malloc(string->length + 1);
    if (bytes == NULL) {
        free(offsets);
        return value_null();
    }
    size_t position = 0;
    for (size_t i = count; i > 0; i--) {
        size_t from = offsets[i - 1];
        size_t length = offsets[i] - from;
        memcpy(bytes + position, string->bytes + from, length);
        position += length;
    }
    bytes[position] = '\0';
    free(offsets);
    return value_string_owned(bytes, position);
}

static Value native_empty_string(Interpreter *interpreter, Value *args, size_t argc) {
    (void)argc;
    if (args[0].type != VAL_STR) {
        runtime_error(interpreter, ERR_INTRPTR006, 0, 0, "emptystr() expects a string");
        return value_null();
    }
    return value_bool(args[0].as.str->length == 0);
}

static const unsigned ARITY_ONE[] = {1};

const NativeEntry string_entries[] = {
    {"strlen", ARITY_ONE, 1, native_strlen, NULL},
    {"reverse", ARITY_ONE, 1, native_reverse, NULL},
    {"emptystr", ARITY_ONE, 1, native_empty_string, NULL}
};

const size_t string_entry_count = sizeof(string_entries) / sizeof(string_entries[0]);
