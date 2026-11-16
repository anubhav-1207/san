#include "lexer.h"

#include "arena.h"
#include "error.h"
#include "table.h"

#include <ctype.h>
#include <stdlib.h>
#include <string.h>

static const char *const SYMBOLS = " !@#$%,^&*(})<>?/{:;|[]+=-`~'\"";

static int current_char(const Lexer *lexer) {
    if (lexer->pos >= lexer->length) {
        return 0;
    }
    return (unsigned char)lexer->source[lexer->pos];
}

static int peek_char(const Lexer *lexer) {
    if (lexer->pos + 1 >= lexer->length) {
        return 0;
    }
    return (unsigned char)lexer->source[lexer->pos + 1];
}

static int advance(Lexer *lexer) {
    int ch = current_char(lexer);
    if (lexer->pos < lexer->length) {
        lexer->pos++;
        lexer->col++;
    }
    return ch;
}

static Token *push_token(Lexer *lexer, TokenType type, int line, int col,
                         size_t start, size_t length) {
    if (lexer->count == lexer->capacity) {
        size_t capacity = lexer->capacity ? lexer->capacity * 2 : 128;
        Token *tokens = arena_alloc(lexer->arena, capacity * sizeof(*tokens));
        if (tokens == NULL) {
            return NULL;
        }
        if (lexer->count > 0) {
            memcpy(tokens, lexer->tokens, lexer->count * sizeof(*tokens));
        }
        lexer->tokens = tokens;
        lexer->capacity = capacity;
    }

    Token *token = &lexer->tokens[lexer->count++];
    memset(token, 0, sizeof(*token));
    token->type = type;
    token->start = lexer->source + start;
    token->length = length;
    token->line = line;
    token->col = col;
    return token;
}

static Token *add_symbol(Lexer *lexer, TokenType type, int line, int col, size_t length) {
    size_t start = lexer->pos;
    for (size_t i = 0; i < length; i++) {
        advance(lexer);
    }
    return push_token(lexer, type, line, col, start, length);
}

static bool is_symbol_char(int ch) {
    return ch != 0 && strchr(SYMBOLS, ch) != NULL;
}

static void read_ident(Lexer *lexer, int line, int col) {
    size_t start = lexer->pos;
    while (current_char(lexer) != 0 &&
           !isspace((unsigned char)current_char(lexer)) &&
           !is_symbol_char(current_char(lexer))) {
        advance(lexer);
    }

    size_t length = lexer->pos - start;
    const char *text = lexer->source + start;
    uint32_t id = strtab_intern(lexer->strings, text, length);

    TokenType type = TT_IDENT;
    bool bool_value = false;
    if (kw_contains(lexer->keywords, id)) {
        type = TT_KEYWORD;
    } else if (length == 4 && memcmp(text, "True", 4) == 0) {
        type = TT_BOOL;
        bool_value = true;
    } else if (length == 5 && memcmp(text, "False", 5) == 0) {
        type = TT_BOOL;
        bool_value = false;
    }

    Token *token = push_token(lexer, type, line, col, start, length);
    if (token != NULL) {
        token->intern_id = id;
        token->bool_value = bool_value;
    }
}

static void read_number(Lexer *lexer, int line, int col) {
    size_t start = lexer->pos;
    while (current_char(lexer) != 0 &&
           (isdigit((unsigned char)current_char(lexer)) || current_char(lexer) == '.')) {
        advance(lexer);
    }

    size_t length = lexer->pos - start;
    const char *text = lexer->source + start;
    int dots = 0;
    for (size_t i = 0; i < length; i++) {
        if (text[i] == '.') {
            dots++;
        }
    }

    if (dots > 1) {
        diags_add(lexer->diags, ERR_LEX004, SAN_PHASE_LEXER, line, col,
                  "invalid float literal '%.*s' — multiple decimal points",
                  (int)length, text);
    }

    TokenType type = dots == 1 ? TT_FLOAT : TT_INT;
    Token *token = push_token(lexer, type, line, col, start, length);
    if (token == NULL) {
        return;
    }

    char *copy = arena_alloc(lexer->arena, length + 1);
    if (copy != NULL) {
        memcpy(copy, text, length);
        copy[length] = '\0';
        if (type == TT_INT) {
            token->int_value = strtoll(copy, NULL, 10);
        } else {
            token->float_value = strtod(copy, NULL);
        }
    }
}

static void read_string(Lexer *lexer, int quote, int line, int col) {
    bool has_closing_quote = false;
    for (size_t i = lexer->pos; i < lexer->length; i++) {
        if (lexer->source[i] == quote) {
            has_closing_quote = true;
            break;
        }
    }

    size_t start = lexer->pos;
    while (current_char(lexer) != 0 && current_char(lexer) != quote &&
           (has_closing_quote || current_char(lexer) != '\n')) {
        if (current_char(lexer) == '\n') {
            advance(lexer);
            lexer->line++;
            lexer->col = 1;
        } else {
            advance(lexer);
        }
    }
    size_t length = lexer->pos - start;

    if (current_char(lexer) == quote) {
        advance(lexer);
    } else {
        diags_add(lexer->diags, ERR_LEX002, SAN_PHASE_LEXER, line, col,
                  "unterminated string literal");
    }
    push_token(lexer, TT_STR, line, col, start, length);
}

static void read_block_comment(Lexer *lexer, int line, int col) {
    advance(lexer);
    advance(lexer);

    for (;;) {
        int ch = current_char(lexer);
        if (ch == 0) {
            diags_add(lexer->diags, ERR_LEX005, SAN_PHASE_LEXER, line, col,
                      "unterminated block comment");
            return;
        }
        if (ch == '*' && peek_char(lexer) == '/') {
            advance(lexer);
            advance(lexer);
            return;
        }
        if (ch == '\n') {
            advance(lexer);
            lexer->line++;
            lexer->col = 1;
        } else {
            advance(lexer);
        }
    }
}

static void invalid_token(Lexer *lexer, int line, int col, int ch) {
    if (ch == '%') {
        diags_add(lexer->diags, ERR_LEX001, SAN_PHASE_LEXER, line, col,
                  "invalid token '%%' — '%%' is not a San operator (use 'div' for floor division)");
    } else {
        diags_add(lexer->diags, ERR_LEX001, SAN_PHASE_LEXER, line, col,
                  "invalid token '%c' in source", ch);
    }
}

void lexer_init(Lexer *lexer, const char *source, size_t length,
                Arena *arena, StringTable *strings, KeywordSet *keywords,
                Diagnostics *diags) {
    lexer->source = source;
    lexer->length = length;
    lexer->pos = 0;
    lexer->line = 1;
    lexer->col = 1;
    lexer->tokens = NULL;
    lexer->count = 0;
    lexer->capacity = 0;
    lexer->arena = arena;
    lexer->strings = strings;
    lexer->keywords = keywords;
    lexer->diags = diags;
}

void lexer_tokenise(Lexer *lexer) {
    while (current_char(lexer) != 0) {
        int ch = current_char(lexer);
        int line = lexer->line;
        int col = lexer->col;

        if (ch == '\n') {
            advance(lexer);
            lexer->line++;
            lexer->col = 1;
            push_token(lexer, TT_NEWLINE, line, col, lexer->pos - 1, 0);
        } else if (isspace((unsigned char)ch)) {
            advance(lexer);
        } else if (ch == '=') {
            if (peek_char(lexer) == '=') {
                add_symbol(lexer, TT_EQEQ, line, col, 2);
            } else {
                add_symbol(lexer, TT_EQ, line, col, 1);
            }
        } else if (ch == '>') {
            if (peek_char(lexer) == '=') {
                add_symbol(lexer, TT_GTE, line, col, 2);
            } else {
                add_symbol(lexer, TT_GT, line, col, 1);
            }
        } else if (ch == '<') {
            if (peek_char(lexer) == '=') {
                add_symbol(lexer, TT_LTE, line, col, 2);
            } else {
                add_symbol(lexer, TT_LT, line, col, 1);
            }
        } else if (ch == '!') {
            if (peek_char(lexer) == '=') {
                add_symbol(lexer, TT_BANGEQ, line, col, 2);
            } else {
                add_symbol(lexer, TT_BANG, line, col, 1);
            }
        } else if (ch == '&' && peek_char(lexer) == '&') {
            add_symbol(lexer, TT_AND, line, col, 2);
        } else if (ch == '|' && peek_char(lexer) == '|') {
            add_symbol(lexer, TT_OR, line, col, 2);
        } else if (ch == '*' && peek_char(lexer) == '*') {
            add_symbol(lexer, TT_STARSTAR, line, col, 2);
        } else if (ch == '*') {
            add_symbol(lexer, TT_STAR, line, col, 1);
        } else if (ch == '/') {
            if (peek_char(lexer) == '/') {
                advance(lexer);
                advance(lexer);
                while (current_char(lexer) != 0 && current_char(lexer) != '\n') {
                    advance(lexer);
                }
            } else if (peek_char(lexer) == '*') {
                read_block_comment(lexer, line, col);
            } else {
                add_symbol(lexer, TT_SLASH, line, col, 1);
            }
        } else if (ch == '(') {
            add_symbol(lexer, TT_LPAREN, line, col, 1);
        } else if (ch == ')') {
            add_symbol(lexer, TT_RPAREN, line, col, 1);
        } else if (ch == '[') {
            add_symbol(lexer, TT_LBRACKET, line, col, 1);
        } else if (ch == ']') {
            add_symbol(lexer, TT_RBRACKET, line, col, 1);
        } else if (ch == '{') {
            add_symbol(lexer, TT_LBRACE, line, col, 1);
        } else if (ch == '}') {
            add_symbol(lexer, TT_RBRACE, line, col, 1);
        } else if (ch == '+') {
            add_symbol(lexer, TT_PLUS, line, col, 1);
        } else if (ch == '-') {
            add_symbol(lexer, TT_MINUS, line, col, 1);
        } else if (ch == '.') {
            add_symbol(lexer, TT_DOT, line, col, 1);
        } else if (ch == ',') {
            add_symbol(lexer, TT_COMMA, line, col, 1);
        } else if (ch == ';') {
            advance(lexer);
        } else if (ch == ':') {
            add_symbol(lexer, TT_COLON, line, col, 1);
        } else if (ch == '$' || ch == '#') {
            advance(lexer);
        } else if (ch == '"' || ch == '\'') {
            advance(lexer);
            read_string(lexer, ch, line, col);
        } else if (isalpha((unsigned char)ch) || ch == '_') {
            read_ident(lexer, line, col);
        } else if (isdigit((unsigned char)ch)) {
            read_number(lexer, line, col);
        } else {
            invalid_token(lexer, line, col, ch);
            advance(lexer);
        }
    }

    push_token(lexer, TT_EOF, lexer->line, lexer->col, lexer->length, 0);
}

const char *token_type_name(TokenType type) {
    switch (type) {
        case TT_INT:       return "INTEGER";
        case TT_FLOAT:     return "FLOAT";
        case TT_BOOL:      return "BOOLEAN";
        case TT_STR:       return "STRING";
        case TT_NULL:      return "NULL";
        case TT_PLUS:      return "PLUS";
        case TT_MINUS:     return "MINUS";
        case TT_SLASH:     return "SLASH";
        case TT_STAR:      return "STAR";
        case TT_STARSTAR:  return "STARSTAR";
        case TT_IN:        return "IN";
        case TT_AND:       return "AND";
        case TT_OR:        return "OR";
        case TT_NOT:       return "NOT";
        case TT_GT:        return "GT";
        case TT_LT:        return "LT";
        case TT_EQ:        return "EQ";
        case TT_GTE:       return "GTE";
        case TT_LTE:       return "LTE";
        case TT_BANG:      return "BANG";
        case TT_BANGEQ:    return "BANGEQ";
        case TT_EQEQ:      return "EQEQ";
        case TT_DOT:       return "DOT";
        case TT_COLON:     return "COLON";
        case TT_SEMICOLON: return "SEMICOLON";
        case TT_COMMA:     return "COMMA";
        case TT_LPAREN:    return "LPAREN";
        case TT_RPAREN:    return "RPAREN";
        case TT_LBRACE:    return "LBRACE";
        case TT_RBRACE:    return "RBRACE";
        case TT_LBRACKET:  return "LBRACKET";
        case TT_RBRACKET:  return "RBRACKET";
        case TT_IDENT:     return "IDENT";
        case TT_KEYWORD:   return "KEYWORD";
        case TT_EOF:       return "EOF";
        case TT_NEWLINE:   return "NEWLINE";
    }
    return "UNKNOWN";
}
