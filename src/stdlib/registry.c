#include "registry.h"

#include "../env.h"
#include "../interpreter.h"
#include "../value.h"

#include <string.h>

static void register_entries(Interpreter *interpreter, const NativeEntry *entries,
                             size_t count) {
    for (size_t i = 0; i < count; i++) {
        uint32_t id = interpreter_intern(interpreter, entries[i].name);
        func_table_add_native(&interpreter->functions, id, &entries[i],
                              entries[i].library == NULL);
    }
}

void stdlib_register(Interpreter *interpreter) {
    register_entries(interpreter, builtin_entries, builtin_entry_count);
    register_entries(interpreter, array_entries, array_entry_count);
    register_entries(interpreter, string_entries, string_entry_count);
    register_entries(interpreter, math_entries, math_entry_count);
    register_entries(interpreter, random_entries, random_entry_count);
    register_entries(interpreter, time_entries, time_entry_count);
}

bool native_arity_ok(const NativeEntry *entry, size_t argc) {
    for (size_t i = 0; i < entry->arity_count; i++) {
        if (entry->arities[i] == argc) return true;
    }
    return false;
}
