#include "registry.h"

#include "../error.h"
#include "../interpreter.h"

#include <stdlib.h>
#include <time.h>

#define MT_N 624
#define MT_M 397
#define MATRIX_A 0x9908b0dfU
#define UPPER_MASK 0x80000000U
#define LOWER_MASK 0x7fffffffU

static uint32_t mt_state[MT_N];
static int mt_index = MT_N + 1;

static void mt_seed(uint32_t seed) {
    mt_state[0] = seed;
    for (int i = 1; i < MT_N; i++) {
        mt_state[i] = 1812433253U * (mt_state[i - 1] ^ (mt_state[i - 1] >> 30)) + (uint32_t)i;
    }
    mt_index = MT_N;
}

static void mt_twist(void) {
    for (int i = 0; i < MT_N; i++) {
        uint32_t y = (mt_state[i] & UPPER_MASK) | (mt_state[(i + 1) % MT_N] & LOWER_MASK);
        mt_state[i] = mt_state[(i + MT_M) % MT_N] ^ (y >> 1);
        if (y & 1U) mt_state[i] ^= MATRIX_A;
    }
    mt_index = 0;
}

static uint32_t mt_uint32(void) {
    if (mt_index >= MT_N) mt_twist();
    uint32_t y = mt_state[mt_index++];
    y ^= y >> 11;
    y ^= (y << 7) & 0x9d2c5680U;
    y ^= (y << 15) & 0xefc60000U;
    y ^= y >> 18;
    return y;
}

static double mt_unit(void) {
    uint32_t a = mt_uint32() >> 6;
    uint32_t b = mt_uint32() >> 5;
    return (a * 67108864.0 + b) / 9007199254740992.0;
}

static void ensure_seeded(void) {
    if (mt_index > MT_N) {
        mt_seed((uint32_t)time(NULL));
    }
}

static bool numeric(const Value *value) {
    return value->type == VAL_INT || value->type == VAL_FLOAT || value->type == VAL_BOOL;
}

static int64_t integer(const Value *value) {
    if (value->type == VAL_BOOL) return value->as.bool_value ? 1 : 0;
    return value->as.int_value;
}

static double number(const Value *value) {
    if (value->type == VAL_BOOL) return value->as.bool_value ? 1.0 : 0.0;
    if (value->type == VAL_INT) return (double)value->as.int_value;
    return value->as.float_value;
}

static Value native_random(Interpreter *interpreter, Value *args, size_t argc) {
    (void)argc;
    ensure_seeded();
    Value *source = &args[0];
    size_t length = 0;
    if (source->type == VAL_STR) length = utf8_count(source->as.str->bytes, source->as.str->length);
    else if (source->type == VAL_ARRAY) length = source->as.array->count;
    else if (source->type == VAL_TUPLE) length = source->as.tuple->count;
    if (length == 0) {
        runtime_error(interpreter, ERR_INTRPTR006, 0, 0, "random() expects a non-empty sequence");
        return value_null();
    }
    size_t index = (size_t)(mt_unit() * (double)length);
    if (index >= length) index = length - 1;
    if (source->type == VAL_STR) {
        size_t from = utf8_byte_offset(source->as.str->bytes, source->as.str->length, index);
        size_t to = utf8_byte_offset(source->as.str->bytes, source->as.str->length, index + 1);
        return value_string(source->as.str->bytes + from, to - from);
    }
    Value item = source->type == VAL_ARRAY ? source->as.array->items[index]
                                           : source->as.tuple->items[index];
    value_retain(&item);
    return item;
}

static Value native_randint(Interpreter *interpreter, Value *args, size_t argc) {
    (void)argc;
    if (!numeric(&args[0]) || !numeric(&args[1])) {
        runtime_error(interpreter, ERR_INTRPTR006, 0, 0, "randint() expects integer arguments");
        return value_null();
    }
    ensure_seeded();
    int64_t low = integer(&args[0]);
    int64_t high = integer(&args[1]);
    if (low > high) {
        runtime_error(interpreter, ERR_INTRPTR006, 0, 0, "randint() start must not exceed end");
        return value_null();
    }
    uint64_t span = (uint64_t)(high - low) + 1;
    uint64_t draw = ((uint64_t)mt_uint32() << 32) | mt_uint32();
    return value_int(low + (int64_t)(draw % span));
}

static Value native_randuniform(Interpreter *interpreter, Value *args, size_t argc) {
    (void)argc;
    if (!numeric(&args[0]) || !numeric(&args[1])) {
        runtime_error(interpreter, ERR_INTRPTR006, 0, 0, "randuniform() expects numeric arguments");
        return value_null();
    }
    ensure_seeded();
    double low = number(&args[0]);
    double high = number(&args[1]);
    return value_float(low + mt_unit() * (high - low));
}

static const unsigned ARITY_ONE[] = {1};
static const unsigned ARITY_TWO[] = {2};

const NativeEntry random_entries[] = {
    {"random", ARITY_ONE, 1, native_random, "random"},
    {"randint", ARITY_TWO, 1, native_randint, "random"},
    {"randuniform", ARITY_TWO, 1, native_randuniform, "random"}
};

const size_t random_entry_count = sizeof(random_entries) / sizeof(random_entries[0]);
