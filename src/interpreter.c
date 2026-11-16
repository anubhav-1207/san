#include "interpreter.h"

#include "stdlib/registry.h"

#include <ctype.h>
#include <math.h>
#include <stdarg.h>
#include <stdlib.h>
#include <string.h>

#define LIB_MATH   1u
#define LIB_RANDOM 2u
#define LIB_TIME   4u

typedef struct {
    char *data;
    size_t length;
    size_t capacity;
} Buf;

void runtime_error(Interpreter *interpreter, ErrorCode code, int line, int col,
                   const char *format, ...) {
    va_list args;
    va_start(args, format);
    char message[256];
    vsnprintf(message, sizeof(message), format, args);
    va_end(args);
    diags_add(interpreter->diags, code, SAN_PHASE_INTERPRETER, line, col, "%s", message);
    interpreter->halted = true;
}

uint32_t interpreter_intern(Interpreter *interpreter, const char *text) {
    return strtab_intern(interpreter->strings, text, strlen(text));
}

void interpreter_init(Interpreter *interpreter, Arena *arena, Diagnostics *diags,
                      StringTable *strings, FILE *input, FILE *output) {
    interpreter->arena = arena;
    interpreter->diags = diags;
    interpreter->strings = strings;
    interpreter->global = env_new(NULL);
    interpreter->current = interpreter->global;
    func_table_init(&interpreter->functions, 64);
    interpreter->libraries = 0;
    interpreter->depth = 0;
    interpreter->halted = false;
    interpreter->input = input;
    interpreter->output = output;
    stdlib_register(interpreter);
}

void interpreter_free(Interpreter *interpreter) {
    func_table_free(&interpreter->functions);
    env_free(interpreter->global);
}

static bool token_eq(const Token *token, const char *text) {
    size_t length = strlen(text);
    return token->length == length && memcmp(token->start, text, length) == 0;
}

static bool is_intlike(const Value *value) {
    return value->type == VAL_INT || value->type == VAL_BOOL;
}

static int64_t as_int(const Value *value) {
    if (value->type == VAL_BOOL) return value->as.bool_value ? 1 : 0;
    return value->as.int_value;
}

static double as_double(const Value *value) {
    if (value->type == VAL_BOOL) return value->as.bool_value ? 1.0 : 0.0;
    if (value->type == VAL_INT) return (double)value->as.int_value;
    return value->as.float_value;
}

static EvalResult make_result(Value value, Flow flow) {
    EvalResult result;
    result.value = value;
    result.flow = flow;
    return result;
}

static Value *lookup_variable(Interpreter *interpreter, const Token *name) {
    Value *value = env_lookup(interpreter->current, name->intern_id);
    if (value == NULL) {
        runtime_error(interpreter, ERR_INTRPTR002, name->line, name->col,
                      "variable '%.*s' is not defined",
                      (int)name->length, name->start);
    }
    return value;
}

static int64_t floor_div_int(int64_t left, int64_t right) {
    int64_t quotient = left / right;
    int64_t remainder = left % right;
    if (remainder != 0 && ((remainder < 0) != (right < 0))) {
        quotient--;
    }
    return quotient;
}

static Value binary_operation(Interpreter *interpreter, const Token *op,
                              Value left, Value right) {
    const char *name = op->start;
    size_t length = op->length;
    int line = op->line;
    int col = op->col;

#define OP_IS(text) (length == strlen(text) && memcmp(name, text, length) == 0)

    if (OP_IS("&&") || OP_IS("||")) {
        bool result = OP_IS("&&")
                          ? (value_truthy(&left) && value_truthy(&right))
                          : (value_truthy(&left) || value_truthy(&right));
        return value_bool(result);
    }

    if (OP_IS("+")) {
        if (is_intlike(&left) && is_intlike(&right)) {
            return value_int(as_int(&left) + as_int(&right));
        }
        if ((left.type == VAL_FLOAT && (is_intlike(&right) || right.type == VAL_FLOAT)) ||
            (right.type == VAL_FLOAT && is_intlike(&left))) {
            return value_float(as_double(&left) + as_double(&right));
        }
        if (left.type == VAL_STR && right.type == VAL_STR) {
            size_t length_left = left.as.str->length;
            size_t length_right = right.as.str->length;
            char *bytes = malloc(length_left + length_right + 1);
            if (bytes == NULL) return value_null();
            memcpy(bytes, left.as.str->bytes, length_left);
            memcpy(bytes + length_left, right.as.str->bytes, length_right);
            bytes[length_left + length_right] = '\0';
            return value_string_owned(bytes, length_left + length_right);
        }
        if (left.type == VAL_ARRAY && right.type == VAL_ARRAY) {
            Value array = value_array(left.as.array->count + right.as.array->count);
            for (size_t i = 0; i < left.as.array->count; i++) {
                Value item = left.as.array->items[i];
                value_retain(&item);
                array.as.array->items[array.as.array->count++] = item;
            }
            for (size_t i = 0; i < right.as.array->count; i++) {
                Value item = right.as.array->items[i];
                value_retain(&item);
                array.as.array->items[array.as.array->count++] = item;
            }
            return array;
        }
    }

    if (OP_IS("-") || OP_IS("*") || OP_IS("/") || OP_IS("div") || OP_IS("**")) {
        bool both_ints = is_intlike(&left) && is_intlike(&right);
        if (OP_IS("*") && ((left.type == VAL_STR && is_intlike(&right)) ||
                           (right.type == VAL_STR && is_intlike(&left)))) {
            Value string = left.type == VAL_STR ? left : right;
            Value count_value = left.type == VAL_STR ? right : left;
            int64_t count = as_int(&count_value);
            if (count <= 0) return value_string("", 0);
            size_t unit = string.as.str->length;
            char *bytes = malloc(unit * (size_t)count + 1);
            if (bytes == NULL) return value_null();
            for (int64_t i = 0; i < count; i++) {
                memcpy(bytes + unit * (size_t)i, string.as.str->bytes, unit);
            }
            bytes[unit * (size_t)count] = '\0';
            return value_string_owned(bytes, unit * (size_t)count);
        }
        if (OP_IS("*") && ((left.type == VAL_ARRAY && is_intlike(&right)) ||
                           (right.type == VAL_ARRAY && is_intlike(&left)))) {
            Value source = left.type == VAL_ARRAY ? left : right;
            Value count_value = left.type == VAL_ARRAY ? right : left;
            int64_t count = as_int(&count_value);
            if (count <= 0) return value_array(0);
            Value array = value_array(source.as.array->count * (size_t)count);
            for (int64_t i = 0; i < count; i++) {
                for (size_t j = 0; j < source.as.array->count; j++) {
                    Value item = source.as.array->items[j];
                    value_retain(&item);
                    array.as.array->items[array.as.array->count++] = item;
                }
            }
            return array;
        }

        if (!((is_intlike(&left) || left.type == VAL_FLOAT) &&
              (is_intlike(&right) || right.type == VAL_FLOAT))) {
            runtime_error(interpreter, ERR_INTRPTR006, line, col,
                          "operation '%.*s' requires numeric operands",
                          (int)length, name);
            return value_null();
        }

        if (OP_IS("/")) {
            double divisor = as_double(&right);
            if (divisor == 0.0) {
                runtime_error(interpreter, ERR_INTRPTR004, line, col,
                              "division by zero in '%.*s'", (int)length, name);
                return value_null();
            }
            return value_float(as_double(&left) / divisor);
        }
        if (OP_IS("div")) {
            if (as_double(&right) == 0.0) {
                runtime_error(interpreter, ERR_INTRPTR004, line, col,
                              "division by zero in 'div'");
                return value_null();
            }
            if (both_ints) {
                return value_int(floor_div_int(as_int(&left), as_int(&right)));
            }
            return value_float(floor(as_double(&left) / as_double(&right)));
        }
        if (OP_IS("**")) {
            if (both_ints && as_int(&right) >= 0) {
                int64_t result = 1;
                int64_t base = as_int(&left);
                int64_t exponent = as_int(&right);
                for (int64_t i = 0; i < exponent; i++) {
                    result *= base;
                }
                return value_int(result);
            }
            if (as_double(&left) == 0.0 && as_double(&right) < 0.0) {
                runtime_error(interpreter, ERR_INTRPTR004, line, col,
                              "zero cannot be raised to a negative power");
                return value_null();
            }
            return value_float(pow(as_double(&left), as_double(&right)));
        }
        if (both_ints) {
            if (OP_IS("-")) return value_int(as_int(&left) - as_int(&right));
            return value_int(as_int(&left) * as_int(&right));
        }
        double a = as_double(&left);
        double b = as_double(&right);
        if (OP_IS("-")) return value_float(a - b);
        return value_float(a * b);
    }

    if (OP_IS("==") || OP_IS("!=")) {
        bool equal = value_equal(&left, &right);
        return value_bool(OP_IS("==") ? equal : !equal);
    }

    if (OP_IS("<") || OP_IS("<=") || OP_IS(">") || OP_IS(">=")) {
        int comparison = 0;
        if ((is_intlike(&left) || left.type == VAL_FLOAT) &&
            (is_intlike(&right) || right.type == VAL_FLOAT)) {
            double a = as_double(&left);
            double b = as_double(&right);
            comparison = a < b ? -1 : (a > b ? 1 : 0);
        } else if (left.type == VAL_STR && right.type == VAL_STR) {
            size_t shortest = left.as.str->length < right.as.str->length
                                  ? left.as.str->length : right.as.str->length;
            comparison = memcmp(left.as.str->bytes, right.as.str->bytes, shortest);
            if (comparison == 0 && left.as.str->length != right.as.str->length) {
                comparison = left.as.str->length < right.as.str->length ? -1 : 1;
            }
        } else {
            runtime_error(interpreter, ERR_INTRPTR006, line, col,
                          "comparison '%.*s' requires comparable operands",
                          (int)length, name);
            return value_null();
        }
        if (OP_IS("<")) return value_bool(comparison < 0);
        if (OP_IS("<=")) return value_bool(comparison <= 0);
        if (OP_IS(">")) return value_bool(comparison > 0);
        return value_bool(comparison >= 0);
    }

    runtime_error(interpreter, ERR_INTRPTR006, line, col,
                  "unsupported operation '%.*s'", (int)length, name);
    return value_null();

#undef OP_IS
}

static size_t sequence_length(const Value *value) {
    if (value->type == VAL_STR) return utf8_count(value->as.str->bytes, value->as.str->length);
    if (value->type == VAL_ARRAY) return value->as.array->count;
    if (value->type == VAL_TUPLE) return value->as.tuple->count;
    return 0;
}

static Value sequence_item(const Value *value, size_t index) {
    if (value->type == VAL_ARRAY) {
        Value item = value->as.array->items[index];
        value_retain(&item);
        return item;
    }
    if (value->type == VAL_TUPLE) {
        Value item = value->as.tuple->items[index];
        value_retain(&item);
        return item;
    }
    size_t start = utf8_byte_offset(value->as.str->bytes, value->as.str->length, index);
    size_t end = utf8_byte_offset(value->as.str->bytes, value->as.str->length, index + 1);
    return value_string(value->as.str->bytes + start, end - start);
}

static Value index_value(Interpreter *interpreter, const Token *op_token,
                         Value *base, Value index) {
    if (!is_intlike(&index)) {
        runtime_error(interpreter, ERR_INTRPTR006, op_token->line, op_token->col,
                      "index must be an integer");
        return value_null();
    }
    size_t length = sequence_length(base);
    if (length == 0 && !(base->type == VAL_STR || base->type == VAL_ARRAY ||
                         base->type == VAL_TUPLE)) {
        runtime_error(interpreter, ERR_INTRPTR006, op_token->line, op_token->col,
                      "value is not indexable");
        return value_null();
    }
    int64_t offset = as_int(&index);
    if (offset < 0) offset += (int64_t)length;
    if (offset < 0 || (size_t)offset >= length) {
        runtime_error(interpreter, ERR_INTRPTR006, op_token->line, op_token->col,
                      "index out of range");
        return value_null();
    }
    return sequence_item(base, (size_t)offset);
}

static void optional_int(Interpreter *interpreter, const AstNode *node,
                         int64_t fallback, bool *provided, int64_t *result) {
    *provided = node != NULL;
    if (node == NULL) {
        *result = fallback;
        return;
    }
    EvalResult evaluated = interpreter_eval(interpreter, node);
    if (!is_intlike(&evaluated.value)) {
        runtime_error(interpreter, ERR_INTRPTR006, node->line, node->col,
                      "slice bounds must be integers");
    } else {
        *result = as_int(&evaluated.value);
    }
    value_release(&evaluated.value);
}

static Value slice_value(Interpreter *interpreter, const Token *op_token,
                         Value *base, const AstNode *start_node,
                         const AstNode *end_node, const AstNode *step_node) {
    size_t length = sequence_length(base);
    int64_t n = (int64_t)length;
    bool has_start, has_end, has_step;
    int64_t start, end, step;
    optional_int(interpreter, step_node, 1, &has_step, &step);
    if (interpreter->halted) return value_null();
    if (step == 0) {
        runtime_error(interpreter, ERR_INTRPTR006, op_token->line, op_token->col,
                      "slice step cannot be zero");
        return value_null();
    }
    optional_int(interpreter, start_node, step > 0 ? 0 : n - 1, &has_start, &start);
    optional_int(interpreter, end_node, step > 0 ? n : -1, &has_end, &end);
    if (interpreter->halted) return value_null();
    (void)has_start;
    (void)has_end;
    (void)has_step;

    if (step > 0) {
        if (start < 0) start += n;
        if (end < 0) end += n;
        if (start < 0) start = 0;
        if (start > n) start = n;
        if (end < 0) end = 0;
        if (end > n) end = n;
    } else {
        if (start < 0) start += n;
        if (end < 0) end += n;
        if (start < 0) start = -1;
        if (start >= n) start = n - 1;
        if (end < -1) end = -1;
        if (end >= n) end = n - 1;
    }

    if (base->type == VAL_STR) {
        Buf bytes = {0};
        for (int64_t i = start; step > 0 ? i < end : i > end; i += step) {
            if (i < 0 || i >= n) continue;
            size_t from = utf8_byte_offset(base->as.str->bytes, base->as.str->length, (size_t)i);
            size_t to = utf8_byte_offset(base->as.str->bytes, base->as.str->length, (size_t)i + 1);
            size_t extra = to - from;
            size_t needed = bytes.length + extra + 1;
            if (needed > bytes.capacity) {
                size_t capacity = bytes.capacity ? bytes.capacity * 2 : 32;
                while (capacity < needed) capacity *= 2;
                char *data = realloc(bytes.data, capacity);
                if (data == NULL) break;
                bytes.data = data;
                bytes.capacity = capacity;
            }
            memcpy(bytes.data + bytes.length, base->as.str->bytes + from, extra);
            bytes.length += extra;
            bytes.data[bytes.length] = '\0';
        }
        if (bytes.data == NULL) return value_string("", 0);
        return value_string_owned(bytes.data, bytes.length);
    }

    Value result = base->type == VAL_TUPLE ? value_tuple(NULL, 0) : value_array(0);
    for (int64_t i = start; step > 0 ? i < end : i > end; i += step) {
        if (i < 0 || i >= n) continue;
        Value item = sequence_item(base, (size_t)i);
        if (result.type == VAL_ARRAY) {
            if (result.as.array->count == result.as.array->capacity) {
                size_t capacity = result.as.array->capacity * 2;
                Value *items = realloc(result.as.array->items, capacity * sizeof(*items));
                if (items == NULL) break;
                result.as.array->items = items;
                result.as.array->capacity = capacity;
            }
            result.as.array->items[result.as.array->count++] = item;
        } else {
            TupleObj *tuple = result.as.tuple;
            Value *items = realloc(tuple->items, (tuple->count + 1) * sizeof(*items));
            if (items == NULL) {
                value_release(&item);
                break;
            }
            tuple->items = items;
            tuple->items[tuple->count++] = item;
        }
    }
    return result;
}

static EvalResult eval_body(Interpreter *interpreter, const AstList *body) {
    Value last = value_null();
    Flow flow = FLOW_NONE;
    for (size_t i = 0; i < body->count; i++) {
        EvalResult evaluated = interpreter_eval(interpreter, body->items[i]);
        value_release(&last);
        last = evaluated.value;
        if (evaluated.flow != FLOW_NONE || interpreter->halted) {
            flow = evaluated.flow;
            break;
        }
    }
    return make_result(last, flow);
}

static EvalResult call_function(Interpreter *interpreter, const Token *name,
                                const AstList *arguments) {
    FuncEntry *entry = func_table_lookup(&interpreter->functions, name->intern_id);
    if (entry == NULL || !entry->enabled) {
        runtime_error(interpreter, ERR_INTRPTR005, name->line, name->col,
                      "function '%.*s' is not defined",
                      (int)name->length, name->start);
        return make_result(value_null(), FLOW_NONE);
    }

    size_t count = arguments->count;
    Value *args = calloc(count ? count : 1, sizeof(*args));
    if (args == NULL) return make_result(value_null(), FLOW_NONE);
    for (size_t i = 0; i < count; i++) {
        EvalResult evaluated = interpreter_eval(interpreter, arguments->items[i]);
        args[i] = evaluated.value;
        if (interpreter->halted) {
            for (size_t j = 0; j <= i; j++) value_release(&args[j]);
            free(args);
            return make_result(value_null(), FLOW_NONE);
        }
    }

    Value result = value_null();
    if (entry->kind == FUNC_NATIVE) {
        if (!native_arity_ok(entry->native, count)) {
            runtime_error(interpreter, ERR_INTRPTR007, name->line, name->col,
                          "function '%.*s' received the wrong number of arguments",
                          (int)name->length, name->start);
        } else {
            result = entry->native->fn(interpreter, args, count);
        }
    } else {
        const AstNode *definition = entry->node;
        if (definition->as.func_def.params.count != count) {
            runtime_error(interpreter, ERR_INTRPTR007, name->line, name->col,
                          "function '%.*s' received the wrong number of arguments",
                          (int)name->length, name->start);
        } else if (interpreter->depth >= SAN_MAX_CALL_DEPTH) {
            runtime_error(interpreter, ERR_INTRPTR008, name->line, name->col,
                          "maximum call depth exceeded while calling '%.*s'",
                          (int)name->length, name->start);
        } else {
            Env *call_env = env_new(interpreter->current);
            for (size_t i = 0; i < count; i++) {
                const Token *param = definition->as.func_def.params.items[i];
                if (interpreter->halted) break;
                size_t before = interpreter->diags->count;
                env_define(call_env, param, args[i], false, interpreter->diags);
                if (interpreter->diags->count != before) interpreter->halted = true;
            }
            if (!interpreter->halted) {
                Env *previous = interpreter->current;
                interpreter->current = call_env;
                interpreter->depth++;
                EvalResult evaluated = eval_body(interpreter, &definition->as.func_def.body);
                interpreter->depth--;
                interpreter->current = previous;
                result = evaluated.value;
                if (evaluated.flow == FLOW_RETURN) {
                    /* return value already owned in result */
                }
            }
            env_free(call_env);
        }
    }

    for (size_t i = 0; i < count; i++) value_release(&args[i]);
    free(args);
    return make_result(result, FLOW_NONE);
}

static EvalResult eval_scan(Interpreter *interpreter, const AstNode *node) {
    char buffer[4096];
    if (fgets(buffer, sizeof(buffer), interpreter->input) == NULL) {
        buffer[0] = '\0';
    }
    size_t length = strlen(buffer);
    while (length > 0 && (buffer[length - 1] == '\n' || buffer[length - 1] == '\r')) {
        buffer[--length] = '\0';
    }

    const Token *type = node->as.scan.type_name;
    const Token *variable = node->as.scan.variable;
    Value value = value_null();
    char *end = NULL;

    if (token_eq(type, "int")) {
        long long parsed = strtoll(buffer, &end, 10);
        if (end == buffer || *end != '\0') {
            runtime_error(interpreter, ERR_INTRPTR006, type->line, type->col,
                          "input '%s' cannot be converted to int", buffer);
        } else {
            value = value_int(parsed);
        }
    } else if (token_eq(type, "float")) {
        double parsed = strtod(buffer, &end);
        if (end == buffer || *end != '\0') {
            runtime_error(interpreter, ERR_INTRPTR006, type->line, type->col,
                          "input '%s' cannot be converted to float", buffer);
        } else {
            value = value_float(parsed);
        }
    } else if (token_eq(type, "str")) {
        value = value_string(buffer, length);
    } else if (token_eq(type, "bool")) {
        if (strcmp(buffer, "true") == 0 || strcmp(buffer, "True") == 0 ||
            strcmp(buffer, "1") == 0) {
            value = value_bool(true);
        } else if (strcmp(buffer, "false") == 0 || strcmp(buffer, "False") == 0 ||
                   strcmp(buffer, "0") == 0) {
            value = value_bool(false);
        } else {
            runtime_error(interpreter, ERR_INTRPTR006, type->line, type->col,
                          "input '%s' cannot be converted to bool", buffer);
        }
    } else {
        value = value_string(buffer, length);
    }

    if (!interpreter->halted) {
        Value *existing = env_lookup(interpreter->current, variable->intern_id);
        size_t before = interpreter->diags->count;
        if (existing != NULL) {
            env_reassign(interpreter->current, variable, value, interpreter->diags);
        } else {
            env_define(interpreter->current, variable, value, false, interpreter->diags);
        }
        if (interpreter->diags->count != before) interpreter->halted = true;
    }
    return make_result(value, FLOW_NONE);
}

static EvalResult eval_for(Interpreter *interpreter, const AstNode *node) {
    EvalResult iterable = interpreter_eval(interpreter, node->as.for_node.iterable);
    if (interpreter->halted) return iterable;

    Env *loop_env = env_new(interpreter->current);
    Env *previous = interpreter->current;
    interpreter->current = loop_env;
    Value result = value_null();
    size_t length = sequence_length(&iterable.value);
    bool variable_defined = false;

    for (size_t i = 0; i < length && !interpreter->halted; i++) {
        Value item = sequence_item(&iterable.value, i);
        size_t before = interpreter->diags->count;
        if (!variable_defined) {
            variable_defined = env_define(loop_env, node->as.for_node.variable,
                                          item, false, interpreter->diags);
        } else {
            env_update_local(loop_env, node->as.for_node.variable, item,
                             interpreter->diags);
        }
        if (interpreter->diags->count != before) interpreter->halted = true;
        value_release(&item);
        EvalResult evaluated = eval_body(interpreter, &node->as.for_node.body);
        value_release(&result);
        result = evaluated.value;
        if (evaluated.flow == FLOW_BREAK) break;
        if (evaluated.flow == FLOW_RETURN) {
            interpreter->current = previous;
            env_free(loop_env);
            value_release(&iterable.value);
            return make_result(result, FLOW_RETURN);
        }
    }

    interpreter->current = previous;
    env_free(loop_env);
    value_release(&iterable.value);
    return make_result(result, FLOW_NONE);
}

EvalResult interpreter_eval(Interpreter *interpreter, const AstNode *node) {
    if (interpreter->halted || node == NULL) {
        return make_result(value_null(), FLOW_NONE);
    }

    switch (node->kind) {
        case AST_NUMBER:
            if (node->as.number.token->type == TT_FLOAT) {
                return make_result(value_float(node->as.number.token->float_value), FLOW_NONE);
            }
            return make_result(value_int(node->as.number.token->int_value), FLOW_NONE);
        case AST_BOOL:
            return make_result(value_bool(node->as.boolean.value), FLOW_NONE);
        case AST_STRING:
            return make_result(value_string(node->as.string.token->start,
                                            node->as.string.token->length), FLOW_NONE);
        case AST_NULL:
            return make_result(value_null(), FLOW_NONE);
        case AST_VAR_ACCESS: {
            Value *value = lookup_variable(interpreter, node->as.var_access.name);
            if (value == NULL) return make_result(value_null(), FLOW_NONE);
            value_retain(value);
            return make_result(*value, FLOW_NONE);
        }
        case AST_VAR_ASSIGN: {
            EvalResult evaluated = interpreter_eval(interpreter, node->as.var_assign.value);
            if (!interpreter->halted) {
                size_t before = interpreter->diags->count;
                env_define(interpreter->current, node->as.var_assign.name,
                           evaluated.value, node->as.var_assign.is_const,
                           interpreter->diags);
                if (interpreter->diags->count != before) interpreter->halted = true;
            }
            return make_result(evaluated.value, FLOW_NONE);
        }
        case AST_VAR_REASSIGN: {
            EvalResult evaluated = interpreter_eval(interpreter, node->as.var_reassign.value);
            if (!interpreter->halted) {
                size_t before = interpreter->diags->count;
                env_reassign(interpreter->current, node->as.var_reassign.name,
                             evaluated.value, interpreter->diags);
                if (interpreter->diags->count != before) interpreter->halted = true;
            }
            return make_result(evaluated.value, FLOW_NONE);
        }
        case AST_UNARY: {
            EvalResult operand = interpreter_eval(interpreter, node->as.unary.operand);
            const Token *op = node->as.unary.op;
            if (interpreter->halted) return operand;
            if (token_eq(op, "!")) {
                bool truth = value_truthy(&operand.value);
                value_release(&operand.value);
                return make_result(value_bool(!truth), FLOW_NONE);
            }
            if (token_eq(op, "-")) {
                if (operand.value.type == VAL_INT) {
                    Value result = value_int(-operand.value.as.int_value);
                    value_release(&operand.value);
                    return make_result(result, FLOW_NONE);
                }
                if (operand.value.type == VAL_FLOAT || operand.value.type == VAL_BOOL) {
                    Value result = value_float(-as_double(&operand.value));
                    value_release(&operand.value);
                    return make_result(result, FLOW_NONE);
                }
            } else if (token_eq(op, "+")) {
                if (is_intlike(&operand.value) || operand.value.type == VAL_FLOAT) {
                    return make_result(operand.value, FLOW_NONE);
                }
            }
            runtime_error(interpreter, ERR_INTRPTR006, op->line, op->col,
                          "unary operator '%.*s' has an invalid operand",
                          (int)op->length, op->start);
            return make_result(operand.value, FLOW_NONE);
        }
        case AST_BINARY: {
            if (token_eq(node->as.binary.op, "&&")) {
                EvalResult left = interpreter_eval(interpreter, node->as.binary.left);
                if (interpreter->halted) return left;
                bool truth = value_truthy(&left.value);
                value_release(&left.value);
                if (!truth) return make_result(value_bool(false), FLOW_NONE);
                EvalResult right = interpreter_eval(interpreter, node->as.binary.right);
                if (interpreter->halted) return right;
                bool result = value_truthy(&right.value);
                value_release(&right.value);
                return make_result(value_bool(result), FLOW_NONE);
            }
            if (token_eq(node->as.binary.op, "||")) {
                EvalResult left = interpreter_eval(interpreter, node->as.binary.left);
                if (interpreter->halted) return left;
                bool truth = value_truthy(&left.value);
                value_release(&left.value);
                if (truth) return make_result(value_bool(true), FLOW_NONE);
                EvalResult right = interpreter_eval(interpreter, node->as.binary.right);
                if (interpreter->halted) return right;
                bool result = value_truthy(&right.value);
                value_release(&right.value);
                return make_result(value_bool(result), FLOW_NONE);
            }
            EvalResult left = interpreter_eval(interpreter, node->as.binary.left);
            if (interpreter->halted) return left;
            EvalResult right = interpreter_eval(interpreter, node->as.binary.right);
            if (interpreter->halted) {
                value_release(&left.value);
                return right;
            }
            Value result = binary_operation(interpreter, node->as.binary.op,
                                            left.value, right.value);
            value_release(&left.value);
            value_release(&right.value);
            return make_result(result, FLOW_NONE);
        }
        case AST_ARRAY: {
            Value array = value_array(node->as.array.elements.count);
            for (size_t i = 0; i < node->as.array.elements.count; i++) {
                EvalResult element = interpreter_eval(interpreter, node->as.array.elements.items[i]);
                if (interpreter->halted) {
                    value_release(&element.value);
                    break;
                }
                array.as.array->items[array.as.array->count++] = element.value;
            }
            return make_result(array, FLOW_NONE);
        }
        case AST_TUPLE: {
            Value *items = calloc(node->as.tuple.elements.count ? node->as.tuple.elements.count : 1,
                                  sizeof(*items));
            size_t count = 0;
            if (items != NULL) {
                for (size_t i = 0; i < node->as.tuple.elements.count; i++) {
                    EvalResult element = interpreter_eval(interpreter, node->as.tuple.elements.items[i]);
                    if (interpreter->halted) {
                        value_release(&element.value);
                        break;
                    }
                    items[count++] = element.value;
                }
            }
            Value tuple = value_tuple(items, count);
            for (size_t i = 0; i < count; i++) value_release(&items[i]);
            free(items);
            return make_result(tuple, FLOW_NONE);
        }
        case AST_INDEX: {
            Value *base = lookup_variable(interpreter, node->as.index.array);
            if (base == NULL) return make_result(value_null(), FLOW_NONE);
            EvalResult index = interpreter_eval(interpreter, node->as.index.start);
            if (interpreter->halted) return index;
            Value result = index_value(interpreter, node->as.index.array, base, index.value);
            value_release(&index.value);
            return make_result(result, FLOW_NONE);
        }
        case AST_SLICE: {
            Value *base = lookup_variable(interpreter, node->as.slice.array);
            if (base == NULL) return make_result(value_null(), FLOW_NONE);
            Value result = slice_value(interpreter, node->as.slice.array, base,
                                       node->as.slice.start, node->as.slice.end,
                                       node->as.slice.step);
            return make_result(result, FLOW_NONE);
        }
        case AST_CALL:
            return call_function(interpreter, node->as.call.name, &node->as.call.args);
        case AST_FUNC_DEF:
            func_table_add_user(&interpreter->functions,
                                node->as.func_def.name->intern_id, node);
            return make_result(value_null(), FLOW_NONE);
        case AST_RETURN: {
            Value value = value_null();
            if (node->as.ret.value != NULL) {
                EvalResult evaluated = interpreter_eval(interpreter, node->as.ret.value);
                value = evaluated.value;
            }
            return make_result(value, FLOW_RETURN);
        }
        case AST_BREAK:
            return make_result(value_null(), FLOW_BREAK);
        case AST_IF: {
            EvalResult condition = interpreter_eval(interpreter, node->as.if_node.condition);
            if (interpreter->halted) return condition;
            bool truth = value_truthy(&condition.value);
            value_release(&condition.value);
            if (truth) return eval_body(interpreter, &node->as.if_node.body);
            for (size_t i = 0; i < node->as.if_node.elif_count; i++) {
                EvalResult elif_condition = interpreter_eval(interpreter,
                                                             node->as.if_node.elifs[i].condition);
                if (interpreter->halted) return elif_condition;
                bool elif_truth = value_truthy(&elif_condition.value);
                value_release(&elif_condition.value);
                if (elif_truth) {
                    return eval_body(interpreter, &node->as.if_node.elifs[i].body);
                }
            }
            if (node->as.if_node.has_else) {
                return eval_body(interpreter, &node->as.if_node.else_body);
            }
            return make_result(value_null(), FLOW_NONE);
        }
        case AST_WHILE: {
            Value result = value_null();
            while (!interpreter->halted) {
                EvalResult condition = interpreter_eval(interpreter, node->as.while_node.condition);
                if (interpreter->halted) {
                    value_release(&condition.value);
                    break;
                }
                bool truth = value_truthy(&condition.value);
                value_release(&condition.value);
                if (!truth) break;
                EvalResult body = eval_body(interpreter, &node->as.while_node.body);
                value_release(&result);
                result = body.value;
                if (body.flow == FLOW_BREAK) break;
                if (body.flow == FLOW_RETURN) return make_result(result, FLOW_RETURN);
            }
            return make_result(result, FLOW_NONE);
        }
        case AST_FOR:
            return eval_for(interpreter, node);
        case AST_SCAN:
            return eval_scan(interpreter, node);
        case AST_USE: {
            const Token *library = node->as.use.library;
            char name[32];
            size_t length = library->length < sizeof(name) - 1 ? library->length : sizeof(name) - 1;
            memcpy(name, library->start, length);
            name[length] = '\0';
            if (strcmp(name, "math") == 0) {
                interpreter->libraries |= LIB_MATH;
                func_table_enable_library(&interpreter->functions, "math");
            } else if (strcmp(name, "random") == 0) {
                interpreter->libraries |= LIB_RANDOM;
                func_table_enable_library(&interpreter->functions, "random");
            } else if (strcmp(name, "time") == 0) {
                interpreter->libraries |= LIB_TIME;
                func_table_enable_library(&interpreter->functions, "time");
            } else {
                runtime_error(interpreter, ERR_INTRPTR007, library->line, library->col,
                              "no built-in library named '%.*s'",
                              (int)library->length, library->start);
            }
            return make_result(value_null(), FLOW_NONE);
        }
        case AST_PROGRAM:
            return eval_body(interpreter, &node->as.program.statements);
        case AST_ERROR:
            return make_result(value_null(), FLOW_NONE);
    }
    return make_result(value_null(), FLOW_NONE);
}

void interpreter_run(Interpreter *interpreter, const AstNode *program) {
    EvalResult result = interpreter_eval(interpreter, program);
    value_release(&result.value);
}
