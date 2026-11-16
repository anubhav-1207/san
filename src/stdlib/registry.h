#ifndef SAN_STDLIB_REGISTRY_H
#define SAN_STDLIB_REGISTRY_H

#include "../san.h"
#include "../value.h"

typedef struct Interpreter Interpreter;

typedef Value (*NativeFn)(Interpreter *interpreter, Value *args, size_t argc);

typedef struct NativeEntry {
    const char *name;
    const unsigned *arities;
    size_t arity_count;
    NativeFn fn;
    const char *library;
} NativeEntry;

extern const NativeEntry builtin_entries[];
extern const size_t builtin_entry_count;
extern const NativeEntry array_entries[];
extern const size_t array_entry_count;
extern const NativeEntry string_entries[];
extern const size_t string_entry_count;
extern const NativeEntry math_entries[];
extern const size_t math_entry_count;
extern const NativeEntry random_entries[];
extern const size_t random_entry_count;
extern const NativeEntry time_entries[];
extern const size_t time_entry_count;

void stdlib_register(Interpreter *interpreter);
bool native_arity_ok(const NativeEntry *entry, size_t argc);

#endif
