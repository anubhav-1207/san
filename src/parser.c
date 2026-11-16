#include "parser.h"

#include "arena.h"

#include <string.h>

void parser_init(Parser *parser, const Token *tokens, size_t count,
                 Arena *arena, Diagnostics *diags) {
    parser->tokens = tokens;
    parser->count = count;
    parser->pos = 0;
    parser->arena = arena;
    parser->diags = diags;
}

static void skip_newlines(Parser *parser) {
    while (parser->pos < parser->count && parser->tokens[parser->pos].type == TT_NEWLINE) {
        parser->pos++;
    }
}

static Token *current(Parser *parser) {
    skip_newlines(parser);
    if (parser->pos >= parser->count) {
        return (Token *)&parser->tokens[parser->count - 1];
    }
    return (Token *)&parser->tokens[parser->pos];
}

static Token *peek(Parser *parser) {
    size_t saved = parser->pos;
    skip_newlines(parser);
    Token *token = (parser->pos + 1 < parser->count)
                       ? (Token *)&parser->tokens[parser->pos + 1]
                       : (Token *)&parser->tokens[parser->count - 1];
    parser->pos = saved;
    return token;
}

static Token *advance_token(Parser *parser) {
    Token *token = current(parser);
    if (parser->pos < parser->count) {
        parser->pos++;
    }
    return token;
}

static bool token_is(const Token *token, const char *text) {
    if (token == NULL) {
        return false;
    }
    size_t length = strlen(text);
    return token->length == length && memcmp(token->start, text, length) == 0;
}

static AstNode *error_node(Parser *parser, const Token *token) {
    return ast_new(parser->arena, AST_ERROR, token->line, token->col);
}

static void unexpected(Parser *parser, const Token *token, const char *expected) {
    diags_add(parser->diags, ERR_PAR001, SAN_PHASE_PARSER, token->line, token->col,
              "unexpected token '%.*s' — expected %s",
              (int)token->length, token->start, expected);
}

static Token *expect_type(Parser *parser, TokenType type, const char *expected) {
    Token *token = current(parser);
    if (token->type != type) {
        unexpected(parser, token, expected);
        return token;
    }
    return advance_token(parser);
}

static Token *expect_value(Parser *parser, const char *value) {
    Token *token = current(parser);
    if (!token_is(token, value)) {
        unexpected(parser, token, value);
        return token;
    }
    return advance_token(parser);
}

static Token *expect_identifier(Parser *parser) {
    Token *token = current(parser);
    if (token->type != TT_IDENT && token->type != TT_KEYWORD) {
        unexpected(parser, token, "an identifier");
        return token;
    }
    return advance_token(parser);
}

static void recover(Parser *parser, size_t start) {
    int depth = 0;
    parser->pos = start;
    while (parser->pos < parser->count) {
        Token *token = (Token *)&parser->tokens[parser->pos];
        if (token->type == TT_EOF) {
            return;
        }
        if (token->type == TT_LPAREN || token->type == TT_LBRACKET ||
            token->type == TT_LBRACE) {
            depth++;
        } else if (token->type == TT_RPAREN || token->type == TT_RBRACKET) {
            if (depth > 0) {
                depth--;
            }
        } else if (token->type == TT_RBRACE) {
            if (depth == 0) {
                return;
            }
            depth--;
        } else if (token->type == TT_NEWLINE && depth == 0) {
            parser->pos++;
            return;
        }
        parser->pos++;
    }
}

static bool infix_binding_power(const Token *token, int *left_bp, int *right_bp) {
    switch (token->type) {
        case TT_OR:
            *left_bp = 1; *right_bp = 2; return true;
        case TT_AND:
            *left_bp = 2; *right_bp = 3; return true;
        case TT_GT:
        case TT_GTE:
        case TT_LT:
        case TT_LTE:
        case TT_EQEQ:
        case TT_BANGEQ:
            *left_bp = 3; *right_bp = 4; return true;
        case TT_PLUS:
        case TT_MINUS:
            *left_bp = 4; *right_bp = 5; return true;
        case TT_STAR:
        case TT_SLASH:
            *left_bp = 5; *right_bp = 6; return true;
        case TT_STARSTAR:
            *left_bp = 6; *right_bp = 6; return true;
        case TT_KEYWORD:
            if (token_is(token, "div")) {
                *left_bp = 5; *right_bp = 6; return true;
            }
            return false;
        default:
            return false;
    }
}

static AstNode *parse_expr(Parser *parser, int min_bp);
static AstNode *parse_statement(Parser *parser);
static AstList parse_block(Parser *parser);

static AstNode *parse_index_or_slice(Parser *parser, const Token *array) {
    AstNode *start = NULL;
    Token *token = current(parser);
    if (token->type != TT_COLON && token->type != TT_RBRACKET &&
        token->type != TT_EOF) {
        start = parse_expr(parser, 0);
    }

    token = current(parser);
    if (token->type == TT_COLON) {
        advance_token(parser);
        AstNode *end = NULL;
        token = current(parser);
        if (token->type != TT_COLON && token->type != TT_RBRACKET &&
            token->type != TT_EOF) {
            end = parse_expr(parser, 0);
        }
        expect_type(parser, TT_COLON, "':'");
        AstNode *step = NULL;
        token = current(parser);
        if (token->type != TT_RBRACKET && token->type != TT_EOF) {
            step = parse_expr(parser, 0);
        }
        expect_type(parser, TT_RBRACKET, "']'");

        AstNode *node = ast_new(parser->arena, AST_SLICE, array->line, array->col);
        node->as.slice.array = array;
        node->as.slice.start = start;
        node->as.slice.end = end;
        node->as.slice.step = step;
        return node;
    }

    expect_type(parser, TT_RBRACKET, "']'");
    AstNode *node = ast_new(parser->arena, AST_INDEX, array->line, array->col);
    node->as.index.array = array;
    node->as.index.start = start;
    return node;
}

static AstNode *parse_primary(Parser *parser) {
    Token *token = current(parser);

    if (token->type == TT_PLUS || token->type == TT_MINUS || token->type == TT_BANG) {
        Token *op = advance_token(parser);
        AstNode *operand = parse_expr(parser, 7);
        AstNode *node = ast_new(parser->arena, AST_UNARY, op->line, op->col);
        node->as.unary.op = op;
        node->as.unary.operand = operand;
        return node;
    }

    if (token->type == TT_INT || token->type == TT_FLOAT) {
        advance_token(parser);
        AstNode *node = ast_new(parser->arena, AST_NUMBER, token->line, token->col);
        node->as.number.token = token;
        return node;
    }

    if (token->type == TT_BOOL) {
        advance_token(parser);
        AstNode *node = ast_new(parser->arena, AST_BOOL, token->line, token->col);
        node->as.boolean.value = token->bool_value;
        return node;
    }

    if (token->type == TT_STR) {
        advance_token(parser);
        AstNode *node = ast_new(parser->arena, AST_STRING, token->line, token->col);
        node->as.string.token = token;
        return node;
    }

    if (token->type == TT_KEYWORD && token_is(token, "Null")) {
        advance_token(parser);
        return ast_new(parser->arena, AST_NULL, token->line, token->col);
    }

    if (token->type == TT_KEYWORD && token_is(token, "flux")) {
        advance_token(parser);
        Token *name = expect_identifier(parser);
        expect_type(parser, TT_EQ, "'='");
        AstNode *value = parse_expr(parser, 0);
        AstNode *node = ast_new(parser->arena, AST_VAR_REASSIGN, token->line, token->col);
        node->as.var_reassign.name = name;
        node->as.var_reassign.value = value;
        return node;
    }

    if (token->type == TT_IDENT) {
        Token *name = advance_token(parser);
        AstNode *base = ast_new(parser->arena, AST_VAR_ACCESS, name->line, name->col);
        base->as.var_access.name = name;

        Token *next = current(parser);
        if (next->type == TT_LPAREN) {
            advance_token(parser);
            AstList args = {0};
            if (current(parser)->type != TT_RPAREN) {
                ast_list_push(parser->arena, &args, parse_expr(parser, 0));
                while (current(parser)->type == TT_COMMA) {
                    advance_token(parser);
                    ast_list_push(parser->arena, &args, parse_expr(parser, 0));
                }
            }
            expect_type(parser, TT_RPAREN, "')'");
            AstNode *call = ast_new(parser->arena, AST_CALL, name->line, name->col);
            call->as.call.name = name;
            call->as.call.args = args;
            return call;
        }
        if (next->type == TT_LBRACKET) {
            advance_token(parser);
            return parse_index_or_slice(parser, name);
        }
        return base;
    }

    if (token->type == TT_LPAREN) {
        advance_token(parser);
        if (current(parser)->type == TT_RPAREN) {
            advance_token(parser);
            return ast_new(parser->arena, AST_TUPLE, token->line, token->col);
        }

        AstNode *first = parse_expr(parser, 0);
        if (current(parser)->type == TT_COMMA) {
            AstNode *tuple = ast_new(parser->arena, AST_TUPLE, token->line, token->col);
            ast_list_push(parser->arena, &tuple->as.tuple.elements, first);
            while (current(parser)->type == TT_COMMA) {
                advance_token(parser);
                Token *after = current(parser);
                if (after->type == TT_RPAREN || after->type == TT_COMMA ||
                    after->type == TT_EOF) {
                    diags_add(parser->diags, ERR_PAR005, SAN_PHASE_PARSER,
                              after->line, after->col, "malformed tuple literal");
                    break;
                }
                ast_list_push(parser->arena, &tuple->as.tuple.elements,
                              parse_expr(parser, 0));
            }
            expect_type(parser, TT_RPAREN, "')'");
            return tuple;
        }
        expect_type(parser, TT_RPAREN, "')'");
        return first;
    }

    if (token->type == TT_LBRACKET) {
        advance_token(parser);
        AstNode *array = ast_new(parser->arena, AST_ARRAY, token->line, token->col);
        if (current(parser)->type != TT_RBRACKET) {
            ast_list_push(parser->arena, &array->as.array.elements, parse_expr(parser, 0));
            while (current(parser)->type == TT_COMMA) {
                advance_token(parser);
                if (current(parser)->type == TT_RBRACKET) {
                    break;
                }
                ast_list_push(parser->arena, &array->as.array.elements,
                              parse_expr(parser, 0));
            }
        }
        expect_type(parser, TT_RBRACKET, "']'");
        return array;
    }

    unexpected(parser, token, "an expression");
    advance_token(parser);
    return error_node(parser, token);
}

static AstNode *parse_expr(Parser *parser, int min_bp) {
    AstNode *left = parse_primary(parser);
    for (;;) {
        Token *op = current(parser);
        int left_bp = 0;
        int right_bp = 0;
        if (!infix_binding_power(op, &left_bp, &right_bp) || left_bp < min_bp) {
            break;
        }
        advance_token(parser);
        AstNode *right = parse_expr(parser, right_bp);
        AstNode *node = ast_new(parser->arena, AST_BINARY, op->line, op->col);
        node->as.binary.left = left;
        node->as.binary.op = op;
        node->as.binary.right = right;
        left = node;
    }
    return left;
}

static AstNode *parse_var_declaration(Parser *parser, bool is_const) {
    Token *keyword = advance_token(parser);
    Token *name = expect_identifier(parser);
    if (current(parser)->type == TT_COLON) {
        advance_token(parser);
        expect_identifier(parser);
    }
    expect_type(parser, TT_EQ, "'='");
    if (is_const && current(parser)->type == TT_LBRACKET) {
        diags_add(parser->diags, ERR_PAR003, SAN_PHASE_PARSER,
                  current(parser)->line, current(parser)->col,
                  "constant '%.*s' cannot be an array",
                  (int)name->length, name->start);
        parser->diags->items[parser->diags->count - 1].class_name = "source.fatal";
    }
    AstNode *value = parse_expr(parser, 0);
    AstNode *node = ast_new(parser->arena, AST_VAR_ASSIGN, keyword->line, keyword->col);
    node->as.var_assign.name = name;
    node->as.var_assign.value = value;
    node->as.var_assign.is_const = is_const;
    return node;
}

static AstNode *parse_if(Parser *parser) {
    Token *keyword = advance_token(parser);
    expect_type(parser, TT_LPAREN, "'('");
    AstNode *condition = parse_expr(parser, 0);
    expect_type(parser, TT_RPAREN, "')'");
    AstList body = parse_block(parser);
    if (body.count == 0) {
        diags_add(parser->diags, ERR_PAR002, SAN_PHASE_PARSER,
                  keyword->line, keyword->col, "empty 'if' body");
    }

    AstNode *node = ast_new(parser->arena, AST_IF, keyword->line, keyword->col);
    node->as.if_node.condition = condition;
    node->as.if_node.body = body;

    while (current(parser)->type == TT_KEYWORD && token_is(current(parser), "elif")) {
        Token *elif_token = advance_token(parser);
        expect_type(parser, TT_LPAREN, "'('");
        AstNode *elif_condition = parse_expr(parser, 0);
        expect_type(parser, TT_RPAREN, "')'");
        AstList elif_body = parse_block(parser);
        if (elif_body.count == 0) {
            diags_add(parser->diags, ERR_PAR002, SAN_PHASE_PARSER,
                      elif_token->line, elif_token->col, "empty 'elif' body");
        }
        ast_elif_push(parser->arena, node, elif_condition, elif_body);
    }

    if (current(parser)->type == TT_KEYWORD && token_is(current(parser), "else")) {
        advance_token(parser);
        node->as.if_node.else_body = parse_block(parser);
        node->as.if_node.has_else = true;
    }
    return node;
}

static AstNode *parse_while(Parser *parser) {
    Token *keyword = advance_token(parser);
    expect_type(parser, TT_LPAREN, "'('");
    AstNode *condition = parse_expr(parser, 0);
    expect_type(parser, TT_RPAREN, "')'");
    AstList body = parse_block(parser);
    if (body.count == 0) {
        diags_add(parser->diags, ERR_PAR002, SAN_PHASE_PARSER,
                  keyword->line, keyword->col, "empty 'while' body");
    }
    AstNode *node = ast_new(parser->arena, AST_WHILE, keyword->line, keyword->col);
    node->as.while_node.condition = condition;
    node->as.while_node.body = body;
    return node;
}

static AstNode *parse_func(Parser *parser) {
    Token *keyword = advance_token(parser);
    Token *name = expect_identifier(parser);
    expect_type(parser, TT_LPAREN, "'('");
    TokenList params = {0};
    if (current(parser)->type != TT_RPAREN) {
        token_list_push(parser->arena, &params, expect_identifier(parser));
        while (current(parser)->type == TT_COMMA) {
            advance_token(parser);
            token_list_push(parser->arena, &params, expect_identifier(parser));
        }
    }
    expect_type(parser, TT_RPAREN, "')'");
    AstList body = parse_block(parser);
    if (body.count == 0) {
        diags_add(parser->diags, ERR_PAR003, SAN_PHASE_PARSER,
                  keyword->line, keyword->col, "empty function body for '%.*s'",
                  (int)name->length, name->start);
    }
    AstNode *node = ast_new(parser->arena, AST_FUNC_DEF, keyword->line, keyword->col);
    node->as.func_def.name = name;
    node->as.func_def.params = params;
    node->as.func_def.body = body;
    return node;
}

static AstNode *parse_for(Parser *parser) {
    Token *keyword = advance_token(parser);
    AstNode *variable = parse_expr(parser, 0);
    expect_value(parser, "in");
    AstNode *iterable = parse_expr(parser, 0);
    AstList body = parse_block(parser);

    const Token *var_token = keyword;
    if (variable != NULL && variable->kind == AST_VAR_ACCESS) {
        var_token = variable->as.var_access.name;
    }
    AstNode *node = ast_new(parser->arena, AST_FOR, keyword->line, keyword->col);
    node->as.for_node.variable = var_token;
    node->as.for_node.iterable = iterable;
    node->as.for_node.body = body;
    return node;
}

static AstNode *parse_scan(Parser *parser) {
    Token *keyword = advance_token(parser);
    expect_type(parser, TT_LPAREN, "'('");
    Token *variable = expect_identifier(parser);
    expect_type(parser, TT_COLON, "':'");
    Token *type_name = expect_identifier(parser);
    expect_type(parser, TT_RPAREN, "')'");
    AstNode *node = ast_new(parser->arena, AST_SCAN, keyword->line, keyword->col);
    node->as.scan.variable = variable;
    node->as.scan.type_name = type_name;
    return node;
}

static AstNode *parse_statement(Parser *parser) {
    Token *token = current(parser);

    if (token->type == TT_KEYWORD && token_is(token, "dec")) {
        return parse_var_declaration(parser, false);
    }
    if (token->type == TT_KEYWORD && token_is(token, "const")) {
        return parse_var_declaration(parser, true);
    }
    if (token->type == TT_KEYWORD && token_is(token, "if")) {
        return parse_if(parser);
    }
    if (token->type == TT_KEYWORD && token_is(token, "while")) {
        return parse_while(parser);
    }
    if (token->type == TT_KEYWORD && token_is(token, "func")) {
        return parse_func(parser);
    }
    if (token->type == TT_KEYWORD && token_is(token, "for")) {
        return parse_for(parser);
    }
    if (token->type == TT_KEYWORD && token_is(token, "return")) {
        Token *keyword = advance_token(parser);
        Token *next = current(parser);
        AstNode *value = NULL;
        if (next->type != TT_EOF && next->type != TT_RBRACE && next->type != TT_NEWLINE) {
            value = parse_expr(parser, 0);
        }
        AstNode *node = ast_new(parser->arena, AST_RETURN, keyword->line, keyword->col);
        node->as.ret.value = value;
        return node;
    }
    if (token->type == TT_KEYWORD && token_is(token, "break")) {
        Token *keyword = advance_token(parser);
        return ast_new(parser->arena, AST_BREAK, keyword->line, keyword->col);
    }
    if (token->type == TT_KEYWORD && token_is(token, "scan")) {
        return parse_scan(parser);
    }
    if (token->type == TT_KEYWORD && token_is(token, "use")) {
        Token *keyword = advance_token(parser);
        Token *library = advance_token(parser);
        AstNode *node = ast_new(parser->arena, AST_USE, keyword->line, keyword->col);
        node->as.use.library = library;
        return node;
    }
    return parse_expr(parser, 0);
}

static AstList parse_block(Parser *parser) {
    AstList body = {0};
    expect_type(parser, TT_LBRACE, "'{'");

    while (current(parser)->type != TT_RBRACE && current(parser)->type != TT_EOF) {
        size_t diagnostics_before = parser->diags->count;
        size_t position_before = parser->pos;
        AstNode *statement = parse_statement(parser);
        ast_list_push(parser->arena, &body, statement);
        if (parser->diags->count != diagnostics_before || parser->pos == position_before) {
            recover(parser, position_before);
        }
    }
    expect_type(parser, TT_RBRACE, "'}'");
    return body;
}

AstNode *parser_parse(Parser *parser) {
    AstNode *program = ast_new(parser->arena, AST_PROGRAM, 1, 1);
    while (current(parser)->type != TT_EOF) {
        size_t diagnostics_before = parser->diags->count;
        size_t position_before = parser->pos;
        AstNode *statement = parse_statement(parser);
        ast_list_push(parser->arena, &program->as.program.statements, statement);
        if (parser->diags->count != diagnostics_before || parser->pos == position_before) {
            recover(parser, position_before);
        }
    }
    return program;
}
