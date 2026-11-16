#include "value.h"

#include <math.h>
#include <stdlib.h>
#include <string.h>

static StringObj *string_alloc(const char *bytes, size_t length) {
    StringObj *obj = malloc(sizeof(*obj));
    if (obj == NULL) {
        return NULL;
    }
    char *copy = malloc(length + 1);
    if (copy == NULL) {
        free(obj);
        return NULL;
    }
    if (length > 0) {
        memcpy(copy, bytes, length);
    }
    copy[length] = '\0';
    obj->refcount = 1;
    obj->bytes = copy;
    obj->length = length;
    return obj;
}

Value value_int(int64_t number) {
    Value value;
    value.type = VAL_INT;
    value.as.int_value = number;
    return value;
}

Value value_float(double number) {
    Value value;
    value.type = VAL_FLOAT;
    value.as.float_value = number;
    return value;
}

Value value_bool(bool boolean) {
    Value value;
    value.type = VAL_BOOL;
    value.as.bool_value = boolean;
    return value;
}

Value value_null(void) {
    Value value;
    value.type = VAL_NULL;
    value.as.int_value = 0;
    return value;
}

Value value_string(const char *bytes, size_t length) {
    Value value = value_null();
    StringObj *obj = string_alloc(bytes, length);
    if (obj != NULL) {
        value.type = VAL_STR;
        value.as.str = obj;
    }
    return value;
}

Value value_string_owned(char *bytes, size_t length) {
    Value value = value_null();
    StringObj *obj = malloc(sizeof(*obj));
    if (obj == NULL) {
        free(bytes);
        return value;
    }
    obj->refcount = 1;
    obj->bytes = bytes;
    obj->length = length;
    value.type = VAL_STR;
    value.as.str = obj;
    return value;
}

Value value_array(size_t capacity) {
    Value value = value_null();
    ArrayObj *obj = malloc(sizeof(*obj));
    if (obj == NULL) {
        return value;
    }
    if (capacity < 4) {
        capacity = 4;
    }
    Value *items = malloc(capacity * sizeof(*items));
    if (items == NULL) {
        free(obj);
        return value;
    }
    obj->refcount = 1;
    obj->items = items;
    obj->count = 0;
    obj->capacity = capacity;
    value.type = VAL_ARRAY;
    value.as.array = obj;
    return value;
}

Value value_tuple(const Value *items, size_t count) {
    Value value = value_null();
    TupleObj *obj = malloc(sizeof(*obj));
    if (obj == NULL) {
        return value;
    }
    Value *copy = malloc((count ? count : 1) * sizeof(*copy));
    if (copy == NULL) {
        free(obj);
        return value;
    }
    for (size_t i = 0; i < count; i++) {
        copy[i] = items[i];
        value_retain(&copy[i]);
    }
    obj->refcount = 1;
    obj->items = copy;
    obj->count = count;
    value.type = VAL_TUPLE;
    value.as.tuple = obj;
    return value;
}

Value value_func(const AstNode *node) {
    Value value = value_null();
    value.type = VAL_FUNC;
    value.as.func = node;
    return value;
}

Value value_native(const NativeEntry *entry) {
    Value value = value_null();
    value.type = VAL_NATIVE;
    value.as.native = entry;
    return value;
}

void value_retain(Value *value) {
    switch (value->type) {
        case VAL_STR:
            if (value->as.str != NULL) value->as.str->refcount++;
            break;
        case VAL_ARRAY:
            if (value->as.array != NULL) value->as.array->refcount++;
            break;
        case VAL_TUPLE:
            if (value->as.tuple != NULL) value->as.tuple->refcount++;
            break;
        default:
            break;
    }
}

void value_release(Value *value) {
    switch (value->type) {
        case VAL_STR:
            if (value->as.str != NULL && --value->as.str->refcount == 0) {
                free(value->as.str->bytes);
                free(value->as.str);
            }
            break;
        case VAL_ARRAY:
            if (value->as.array != NULL && --value->as.array->refcount == 0) {
                for (size_t i = 0; i < value->as.array->count; i++) {
                    value_release(&value->as.array->items[i]);
                }
                free(value->as.array->items);
                free(value->as.array);
            }
            break;
        case VAL_TUPLE:
            if (value->as.tuple != NULL && --value->as.tuple->refcount == 0) {
                for (size_t i = 0; i < value->as.tuple->count; i++) {
                    value_release(&value->as.tuple->items[i]);
                }
                free(value->as.tuple->items);
                free(value->as.tuple);
            }
            break;
        default:
            break;
    }
    value->type = VAL_NULL;
    value->as.int_value = 0;
}

bool value_truthy(const Value *value) {
    switch (value->type) {
        case VAL_NULL:
            return false;
        case VAL_BOOL:
            return value->as.bool_value;
        case VAL_INT:
            return value->as.int_value != 0;
        case VAL_FLOAT:
            return value->as.float_value != 0.0;
        case VAL_STR:
            return value->as.str != NULL && value->as.str->length != 0;
        case VAL_ARRAY:
            return value->as.array != NULL && value->as.array->count != 0;
        case VAL_TUPLE:
            return value->as.tuple != NULL && value->as.tuple->count != 0;
        default:
            return true;
    }
}

static double numeric_value(const Value *value) {
    switch (value->type) {
        case VAL_BOOL:
            return value->as.bool_value ? 1.0 : 0.0;
        case VAL_INT:
            return (double)value->as.int_value;
        case VAL_FLOAT:
            return value->as.float_value;
        default:
            return 0.0;
    }
}

static bool is_numeric(const Value *value) {
    return value->type == VAL_INT || value->type == VAL_FLOAT || value->type == VAL_BOOL;
}

bool value_equal(const Value *left, const Value *right) {
    if (is_numeric(left) && is_numeric(right)) {
        return numeric_value(left) == numeric_value(right);
    }
    if (left->type != right->type) {
        return false;
    }
    switch (left->type) {
        case VAL_NULL:
            return true;
        case VAL_STR:
            return left->as.str->length == right->as.str->length &&
                   memcmp(left->as.str->bytes, right->as.str->bytes, left->as.str->length) == 0;
        case VAL_ARRAY:
            if (left->as.array->count != right->as.array->count) return false;
            for (size_t i = 0; i < left->as.array->count; i++) {
                if (!value_equal(&left->as.array->items[i], &right->as.array->items[i])) return false;
            }
            return true;
        case VAL_TUPLE:
            if (left->as.tuple->count != right->as.tuple->count) return false;
            for (size_t i = 0; i < left->as.tuple->count; i++) {
                if (!value_equal(&left->as.tuple->items[i], &right->as.tuple->items[i])) return false;
            }
            return true;
        default:
            return false;
    }
}

typedef struct {
    char *data;
    size_t length;
    size_t capacity;
} Buf;

static void buf_reserve(Buf *buf, size_t extra) {
    if (buf->length + extra + 1 <= buf->capacity) {
        return;
    }
    size_t capacity = buf->capacity ? buf->capacity * 2 : 32;
    while (capacity < buf->length + extra + 1) {
        capacity *= 2;
    }
    char *data = realloc(buf->data, capacity);
    if (data == NULL) {
        return;
    }
    buf->data = data;
    buf->capacity = capacity;
}

static void buf_putc(Buf *buf, char ch) {
    buf_reserve(buf, 1);
    if (buf->data != NULL) {
        buf->data[buf->length++] = ch;
        buf->data[buf->length] = '\0';
    }
}

static void buf_puts(Buf *buf, const char *text) {
    size_t length = strlen(text);
    buf_reserve(buf, length);
    if (buf->data != NULL) {
        memcpy(buf->data + buf->length, text, length);
        buf->length += length;
        buf->data[buf->length] = '\0';
    }
}

static void format_double(char *buffer, size_t size, double number) {
    if (isnan(number)) {
        snprintf(buffer, size, "nan");
        return;
    }
    if (isinf(number)) {
        snprintf(buffer, size, number < 0 ? "-inf" : "inf");
        return;
    }
    for (int precision = 15; precision <= 17; precision++) {
        snprintf(buffer, size, "%.*g", precision, number);
        if (strtod(buffer, NULL) == number) {
            break;
        }
    }
    if (strchr(buffer, '.') == NULL && strchr(buffer, 'e') == NULL &&
        strchr(buffer, 'E') == NULL) {
        strncat(buffer, ".0", size - strlen(buffer) - 1);
    }
}

static void repr_string(Buf *buf, const StringObj *string) {
    const char *bytes = string->bytes;
    char quote = '\'';
    if (memchr(bytes, '\'', string->length) != NULL &&
        memchr(bytes, '"', string->length) == NULL) {
        quote = '"';
    }
    buf_putc(buf, quote);
    for (size_t i = 0; i < string->length; i++) {
        unsigned char ch = (unsigned char)bytes[i];
        if (ch == quote || ch == '\\') {
            buf_putc(buf, '\\');
            buf_putc(buf, (char)ch);
        } else if (ch == '\n') {
            buf_puts(buf, "\\n");
        } else if (ch == '\r') {
            buf_puts(buf, "\\r");
        } else if (ch == '\t') {
            buf_puts(buf, "\\t");
        } else if (ch < 0x20 || ch == 0x7f) {
            char escaped[8];
            snprintf(escaped, sizeof(escaped), "\\x%02x", ch);
            buf_puts(buf, escaped);
        } else {
            buf_putc(buf, (char)ch);
        }
    }
    buf_putc(buf, quote);
}

static void repr_impl(Buf *buf, const Value *value) {
    char number[64];
    switch (value->type) {
        case VAL_INT:
            snprintf(number, sizeof(number), "%lld", (long long)value->as.int_value);
            buf_puts(buf, number);
            break;
        case VAL_FLOAT:
            format_double(number, sizeof(number), value->as.float_value);
            buf_puts(buf, number);
            break;
        case VAL_BOOL:
            buf_puts(buf, value->as.bool_value ? "True" : "False");
            break;
        case VAL_NULL:
            buf_puts(buf, "None");
            break;
        case VAL_STR:
            if (value->as.str != NULL) {
                repr_string(buf, value->as.str);
            }
            break;
        case VAL_ARRAY:
            buf_putc(buf, '[');
            if (value->as.array != NULL) {
                for (size_t i = 0; i < value->as.array->count; i++) {
                    if (i > 0) buf_puts(buf, ", ");
                    repr_impl(buf, &value->as.array->items[i]);
                }
            }
            buf_putc(buf, ']');
            break;
        case VAL_TUPLE:
            buf_putc(buf, '(');
            if (value->as.tuple != NULL) {
                for (size_t i = 0; i < value->as.tuple->count; i++) {
                    if (i > 0) buf_puts(buf, ", ");
                    repr_impl(buf, &value->as.tuple->items[i]);
                }
                if (value->as.tuple->count == 1) buf_putc(buf, ',');
            }
            buf_putc(buf, ')');
            break;
        case VAL_FUNC:
            buf_puts(buf, "<func>");
            break;
        case VAL_NATIVE:
            buf_puts(buf, "<native>");
            break;
    }
}

void value_display(FILE *stream, const Value *value) {
    if (value->type == VAL_STR && value->as.str != NULL) {
        fwrite(value->as.str->bytes, 1, value->as.str->length, stream);
        return;
    }
    Buf buf = {0};
    repr_impl(&buf, value);
    if (buf.data != NULL) {
        fwrite(buf.data, 1, buf.length, stream);
        free(buf.data);
    }
}

void value_repr(FILE *stream, const Value *value) {
    Buf buf = {0};
    repr_impl(&buf, value);
    if (buf.data != NULL) {
        fwrite(buf.data, 1, buf.length, stream);
        free(buf.data);
    }
}

Value value_to_string(const Value *value) {
    Buf buf = {0};
    if (value->type == VAL_STR) {
        if (value->as.str != NULL) {
            buf_reserve(&buf, value->as.str->length);
            if (buf.data != NULL) {
                memcpy(buf.data, value->as.str->bytes, value->as.str->length);
                buf.length = value->as.str->length;
                buf.data[buf.length] = '\0';
            }
        }
    } else {
        repr_impl(&buf, value);
    }
    if (buf.data == NULL) {
        return value_string("", 0);
    }
    return value_string_owned(buf.data, buf.length);
}

static size_t utf8_sequence_length(unsigned char lead) {
    if (lead < 0x80) return 1;
    if ((lead & 0xe0) == 0xc0) return 2;
    if ((lead & 0xf0) == 0xe0) return 3;
    if ((lead & 0xf8) == 0xf0) return 4;
    return 1;
}

size_t utf8_count(const char *bytes, size_t length) {
    size_t count = 0;
    size_t i = 0;
    while (i < length) {
        size_t step = utf8_sequence_length((unsigned char)bytes[i]);
        if (i + step > length) step = 1;
        i += step;
        count++;
    }
    return count;
}

size_t utf8_byte_offset(const char *bytes, size_t length, size_t index) {
    size_t count = 0;
    size_t i = 0;
    while (i < length) {
        if (count == index) {
            return i;
        }
        size_t step = utf8_sequence_length((unsigned char)bytes[i]);
        if (i + step > length) step = 1;
        i += step;
        count++;
    }
    return length;
}

const char *value_type_name(ValueType type) {
    switch (type) {
        case VAL_INT:    return "int";
        case VAL_FLOAT:  return "float";
        case VAL_BOOL:   return "bool";
        case VAL_STR:    return "str";
        case VAL_ARRAY:  return "array";
        case VAL_TUPLE:  return "tuple";
        case VAL_NULL:   return "null";
        case VAL_FUNC:   return "func";
        case VAL_NATIVE: return "native";
    }
    return "null";
}
