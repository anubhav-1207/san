#ifndef SAN_AST_H
#define SAN_AST_H

#include "san.h"
#include "lexer.h"

#include <stdio.h>

typedef enum {
    AST_PROGRAM,
    AST_NUMBER,
    AST_BOOL,
    AST_STRING,
    AST_NULL,
    AST_UNARY,
    AST_BINARY,
    AST_VAR_ASSIGN,
    AST_VAR_REASSIGN,
    AST_VAR_ACCESS,
    AST_ARRAY,
    AST_INDEX,
    AST_SLICE,
    AST_TUPLE,
    AST_CALL,
    AST_FUNC_DEF,
    AST_RETURN,
    AST_BREAK,
    AST_IF,
    AST_WHILE,
    AST_FOR,
    AST_SCAN,
    AST_USE,
    AST_ERROR
} AstKind;

typedef struct AstNode AstNode;

typedef struct {
    AstNode **items;
    size_t count;
    size_t capacity;
} AstList;

typedef struct {
    const Token **items;
    size_t count;
    size_t capacity;
} TokenList;

typedef struct {
    AstNode *condition;
    AstList body;
} AstElif;

struct AstNode {
    AstKind kind;
    int line;
    int col;
    union {
        struct { AstList statements; } program;
        struct { const Token *token; } number;
        struct { bool value; } boolean;
        struct { const Token *token; } string;
        struct { const Token *op; AstNode *operand; } unary;
        struct { AstNode *left; const Token *op; AstNode *right; } binary;
        struct { const Token *name; AstNode *value; bool is_const; } var_assign;
        struct { const Token *name; AstNode *value; } var_reassign;
        struct { const Token *name; } var_access;
        struct { AstList elements; } array;
        struct { const Token *array; AstNode *start; } index;
        struct { const Token *array; AstNode *start; AstNode *end; AstNode *step; } slice;
        struct { AstList elements; } tuple;
        struct { const Token *name; AstList args; } call;
        struct { const Token *name; TokenList params; AstList body; } func_def;
        struct { AstNode *value; } ret;
        struct {
            AstNode *condition;
            AstList body;
            AstElif *elifs;
            size_t elif_count;
            size_t elif_capacity;
            AstList else_body;
            bool has_else;
        } if_node;
        struct { AstNode *condition; AstList body; } while_node;
        struct { const Token *variable; AstNode *iterable; AstList body; } for_node;
        struct { const Token *variable; const Token *type_name; } scan;
        struct { const Token *library; } use;
    } as;
};

AstNode *ast_new(Arena *arena, AstKind kind, int line, int col);
void ast_list_push(Arena *arena, AstList *list, AstNode *node);
void token_list_push(Arena *arena, TokenList *list, const Token *token);
void ast_elif_push(Arena *arena, AstNode *node, AstNode *condition, AstList body);
void ast_print(FILE *stream, const AstNode *node);

#endif
