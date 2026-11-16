#ifndef SAN_ENV_H
#define SAN_ENV_H

#include "san.h"
#include "ast.h"
#include "error.h"
#include "lexer.h"
#include "value.h"

typedef struct NativeEntry NativeEntry;

typedef struct Binding {
    uint32_t name_id;
    Value value;
    bool is_const;
    struct Binding *next;
} Binding;

struct Env {
    struct Env *parent;
    Binding **buckets;
    size_t capacity;
    size_t count;
};

typedef enum {
    FUNC_USER,
    FUNC_NATIVE
} FuncKind;

typedef struct FuncEntry {
    uint32_t name_id;
    FuncKind kind;
    const AstNode *node;
    const NativeEntry *native;
    bool enabled;
    struct FuncEntry *next;
} FuncEntry;

typedef struct {
    FuncEntry **buckets;
    size_t capacity;
    size_t count;
} FuncTable;

Env *env_new(Env *parent);
void env_free(Env *env);
bool env_define(Env *env, const Token *name, Value value, bool is_const,
                Diagnostics *diags);
Value *env_lookup(Env *env, uint32_t name_id);
bool env_reassign(Env *env, const Token *name, Value value, Diagnostics *diags);
bool env_update_local(Env *env, const Token *name, Value value, Diagnostics *diags);

void func_table_init(FuncTable *table, size_t capacity);
void func_table_free(FuncTable *table);
FuncEntry *func_table_lookup(FuncTable *table, uint32_t name_id);
FuncEntry *func_table_add_user(FuncTable *table, uint32_t name_id, const AstNode *node);
FuncEntry *func_table_add_native(FuncTable *table, uint32_t name_id,
                                 const NativeEntry *native, bool enabled);
void func_table_enable_library(FuncTable *table, const char *library);

#endif
