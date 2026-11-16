#include "env.h"

#include "stdlib/registry.h"

#include <stdlib.h>
#include <string.h>

static size_t hash_id(uint32_t id) {
    uint64_t hash = 1469598103934665603ULL;
    hash ^= id;
    hash *= 1099511628211ULL;
    return (size_t)hash;
}

Env *env_new(Env *parent) {
    Env *env = malloc(sizeof(*env));
    if (env == NULL) {
        return NULL;
    }
    size_t capacity = 16;
    env->buckets = calloc(capacity, sizeof(*env->buckets));
    if (env->buckets == NULL) {
        free(env);
        return NULL;
    }
    env->parent = parent;
    env->capacity = capacity;
    env->count = 0;
    return env;
}

void env_free(Env *env) {
    if (env == NULL) {
        return;
    }
    for (size_t i = 0; i < env->capacity; i++) {
        Binding *binding = env->buckets[i];
        while (binding != NULL) {
            Binding *next = binding->next;
            value_release(&binding->value);
            free(binding);
            binding = next;
        }
    }
    free(env->buckets);
    free(env);
}

static void env_grow(Env *env) {
    size_t capacity = env->capacity * 2;
    Binding **buckets = calloc(capacity, sizeof(*buckets));
    if (buckets == NULL) {
        return;
    }
    for (size_t i = 0; i < env->capacity; i++) {
        Binding *binding = env->buckets[i];
        while (binding != NULL) {
            Binding *next = binding->next;
            size_t slot = hash_id(binding->name_id) & (capacity - 1);
            binding->next = buckets[slot];
            buckets[slot] = binding;
            binding = next;
        }
    }
    free(env->buckets);
    env->buckets = buckets;
    env->capacity = capacity;
}

bool env_define(Env *env, const Token *name, Value value, bool is_const,
                Diagnostics *diags) {
    size_t slot = hash_id(name->intern_id) & (env->capacity - 1);
    for (Binding *binding = env->buckets[slot]; binding != NULL; binding = binding->next) {
        if (binding->name_id == name->intern_id) {
            diags_add(diags, ERR_INTRPTR001, SAN_PHASE_INTERPRETER,
                      name->line, name->col,
                      "variable '%.*s' is already defined",
                      (int)name->length, name->start);
            return false;
        }
    }

    Binding *binding = malloc(sizeof(*binding));
    if (binding == NULL) {
        return false;
    }
    binding->name_id = name->intern_id;
    binding->value = value;
    binding->is_const = is_const;
    binding->next = env->buckets[slot];
    env->buckets[slot] = binding;
    env->count++;
    value_retain(&value);

    if (env->count * 10 >= env->capacity * 7) {
        env_grow(env);
    }
    return true;
}

Value *env_lookup(Env *env, uint32_t name_id) {
    for (Env *scope = env; scope != NULL; scope = scope->parent) {
        size_t slot = hash_id(name_id) & (scope->capacity - 1);
        for (Binding *binding = scope->buckets[slot]; binding != NULL;
             binding = binding->next) {
            if (binding->name_id == name_id) {
                return &binding->value;
            }
        }
    }
    return NULL;
}

static void const_error(Diagnostics *diags, const Token *name) {
    diags_add(diags, ERR_INTRPTR003, SAN_PHASE_INTERPRETER,
              name->line, name->col,
              "constant '%.*s' cannot be reassigned",
              (int)name->length, name->start);
}

bool env_reassign(Env *env, const Token *name, Value value, Diagnostics *diags) {
    for (Env *scope = env; scope != NULL; scope = scope->parent) {
        size_t slot = hash_id(name->intern_id) & (scope->capacity - 1);
        for (Binding *binding = scope->buckets[slot]; binding != NULL;
             binding = binding->next) {
            if (binding->name_id == name->intern_id) {
                if (binding->is_const) {
                    const_error(diags, name);
                    return false;
                }
                value_release(&binding->value);
                binding->value = value;
                value_retain(&value);
                return true;
            }
        }
    }
    diags_add(diags, ERR_INTRPTR002, SAN_PHASE_INTERPRETER,
              name->line, name->col,
              "variable '%.*s' is not defined",
              (int)name->length, name->start);
    return false;
}

bool env_update_local(Env *env, const Token *name, Value value, Diagnostics *diags) {
    size_t slot = hash_id(name->intern_id) & (env->capacity - 1);
    for (Binding *binding = env->buckets[slot]; binding != NULL; binding = binding->next) {
        if (binding->name_id == name->intern_id) {
            value_release(&binding->value);
            binding->value = value;
            value_retain(&value);
            return true;
        }
    }
    diags_add(diags, ERR_INTRPTR002, SAN_PHASE_INTERPRETER,
              name->line, name->col,
              "variable '%.*s' is not defined",
              (int)name->length, name->start);
    return false;
}

void func_table_init(FuncTable *table, size_t capacity) {
    if (capacity < 8) capacity = 8;
    table->buckets = calloc(capacity, sizeof(*table->buckets));
    table->capacity = capacity;
    table->count = 0;
}

void func_table_free(FuncTable *table) {
    if (table->buckets == NULL) return;
    for (size_t i = 0; i < table->capacity; i++) {
        FuncEntry *entry = table->buckets[i];
        while (entry != NULL) {
            FuncEntry *next = entry->next;
            free(entry);
            entry = next;
        }
    }
    free(table->buckets);
    table->buckets = NULL;
    table->capacity = 0;
}

static void func_table_grow(FuncTable *table) {
    size_t capacity = table->capacity * 2;
    FuncEntry **buckets = calloc(capacity, sizeof(*buckets));
    if (buckets == NULL) return;
    for (size_t i = 0; i < table->capacity; i++) {
        FuncEntry *entry = table->buckets[i];
        while (entry != NULL) {
            FuncEntry *next = entry->next;
            size_t slot = hash_id(entry->name_id) & (capacity - 1);
            entry->next = buckets[slot];
            buckets[slot] = entry;
            entry = next;
        }
    }
    free(table->buckets);
    table->buckets = buckets;
    table->capacity = capacity;
}

FuncEntry *func_table_lookup(FuncTable *table, uint32_t name_id) {
    size_t slot = hash_id(name_id) & (table->capacity - 1);
    for (FuncEntry *entry = table->buckets[slot]; entry != NULL; entry = entry->next) {
        if (entry->name_id == name_id) {
            return entry;
        }
    }
    return NULL;
}

static FuncEntry *func_table_insert(FuncTable *table, uint32_t name_id) {
    FuncEntry *existing = func_table_lookup(table, name_id);
    if (existing != NULL) {
        return existing;
    }
    FuncEntry *entry = malloc(sizeof(*entry));
    if (entry == NULL) {
        return NULL;
    }
    entry->name_id = name_id;
    entry->node = NULL;
    entry->native = NULL;
    entry->enabled = true;
    size_t slot = hash_id(name_id) & (table->capacity - 1);
    entry->next = table->buckets[slot];
    table->buckets[slot] = entry;
    table->count++;
    if (table->count * 10 >= table->capacity * 7) {
        func_table_grow(table);
    }
    return entry;
}

FuncEntry *func_table_add_user(FuncTable *table, uint32_t name_id, const AstNode *node) {
    FuncEntry *entry = func_table_insert(table, name_id);
    if (entry != NULL) {
        entry->kind = FUNC_USER;
        entry->node = node;
        entry->native = NULL;
        entry->enabled = true;
    }
    return entry;
}

void func_table_enable_library(FuncTable *table, const char *library) {
    if (table->buckets == NULL) return;
    for (size_t i = 0; i < table->capacity; i++) {
        for (FuncEntry *entry = table->buckets[i]; entry != NULL; entry = entry->next) {
            if (entry->kind == FUNC_NATIVE && entry->native != NULL &&
                entry->native->library != NULL &&
                strcmp(entry->native->library, library) == 0) {
                entry->enabled = true;
            }
        }
    }
}

FuncEntry *func_table_add_native(FuncTable *table, uint32_t name_id,
                                 const NativeEntry *native, bool enabled) {
    FuncEntry *entry = func_table_insert(table, name_id);
    if (entry != NULL) {
        entry->kind = FUNC_NATIVE;
        entry->node = NULL;
        entry->native = native;
        entry->enabled = enabled;
    }
    return entry;
}
