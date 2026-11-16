#ifndef SAN_INTERPRETER_H
#define SAN_INTERPRETER_H

#include "san.h"
#include "ast.h"
#include "env.h"
#include "error.h"
#include "table.h"
#include "value.h"

#include <stdio.h>

#define SAN_MAX_CALL_DEPTH 2048

typedef struct Interpreter Interpreter;

typedef enum {
    FLOW_NONE = 0,
    FLOW_BREAK,
    FLOW_RETURN
} Flow;

typedef struct {
    Value value;
    Flow flow;
} EvalResult;

struct Interpreter {
    Arena *arena;
    Diagnostics *diags;
    StringTable *strings;
    Env *global;
    Env *current;
    FuncTable functions;
    unsigned libraries;
    int depth;
    bool halted;
    FILE *input;
    FILE *output;
};

void interpreter_init(Interpreter *interpreter, Arena *arena, Diagnostics *diags,
                      StringTable *strings, FILE *input, FILE *output);
void interpreter_free(Interpreter *interpreter);
EvalResult interpreter_eval(Interpreter *interpreter, const AstNode *node);
void interpreter_run(Interpreter *interpreter, const AstNode *program);
void runtime_error(Interpreter *interpreter, ErrorCode code, int line, int col,
                   const char *format, ...);
uint32_t interpreter_intern(Interpreter *interpreter, const char *text);

#endif
