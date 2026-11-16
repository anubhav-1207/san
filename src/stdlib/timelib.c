#define _POSIX_C_SOURCE 200809L

#include "registry.h"

#include "../error.h"
#include "../interpreter.h"

#include <string.h>
#include <time.h>

static Value native_time(Interpreter *interpreter, Value *args, size_t argc) {
    (void)interpreter;
    (void)args;
    (void)argc;
    struct timespec now;
    if (clock_gettime(CLOCK_REALTIME, &now) != 0) {
        return value_float((double)time(NULL));
    }
    return value_float((double)now.tv_sec + (double)now.tv_nsec / 1000000000.0);
}

static Value native_timesleep(Interpreter *interpreter, Value *args, size_t argc) {
    (void)argc;
    double duration = 0.0;
    Value *value = &args[0];
    if (value->type == VAL_INT) duration = (double)value->as.int_value;
    else if (value->type == VAL_FLOAT) duration = value->as.float_value;
    else if (value->type == VAL_BOOL) duration = value->as.bool_value ? 1.0 : 0.0;
    else {
        runtime_error(interpreter, ERR_INTRPTR006, 0, 0, "timesleep() expects a number");
        return value_null();
    }
    if (duration <= 0.0) return value_null();
    struct timespec request;
    request.tv_sec = (time_t)duration;
    request.tv_nsec = (long)((duration - (double)request.tv_sec) * 1000000000.0);
    while (nanosleep(&request, &request) != 0) {
        /* interrupted by a signal: continue sleeping */
    }
    return value_null();
}

static Value native_structime(Interpreter *interpreter, Value *args, size_t argc) {
    (void)interpreter;
    (void)args;
    (void)argc;
    time_t now = time(NULL);
    char *text = ctime(&now);
    if (text == NULL) return value_string("", 0);
    size_t length = strlen(text);
    while (length > 0 && text[length - 1] == '\n') length--;
    return value_string(text, length);
}

static const unsigned ARITY_ZERO[] = {0};
static const unsigned ARITY_ONE[] = {1};

const NativeEntry time_entries[] = {
    {"time", ARITY_ZERO, 1, native_time, "time"},
    {"timesleep", ARITY_ONE, 1, native_timesleep, "time"},
    {"structime", ARITY_ZERO, 1, native_structime, "time"}
};

const size_t time_entry_count = sizeof(time_entries) / sizeof(time_entries[0]);
