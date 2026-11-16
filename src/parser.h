#ifndef SAN_PARSER_H
#define SAN_PARSER_H

#include "san.h"
#include "ast.h"
#include "error.h"
#include "lexer.h"

typedef struct {
    const Token *tokens;
    size_t count;
    size_t pos;
    Arena *arena;
    Diagnostics *diags;
} Parser;

void parser_init(Parser *parser, const Token *tokens, size_t count,
                 Arena *arena, Diagnostics *diags);
AstNode *parser_parse(Parser *parser);

#endif
