#ifndef SAN_LEXER_H
#define SAN_LEXER_H

#include "san.h"

typedef enum {
    TT_INT,
    TT_FLOAT,
    TT_BOOL,
    TT_STR,
    TT_NULL,
    TT_PLUS,
    TT_MINUS,
    TT_SLASH,
    TT_STAR,
    TT_STARSTAR,
    TT_IN,
    TT_AND,
    TT_OR,
    TT_NOT,
    TT_GT,
    TT_LT,
    TT_EQ,
    TT_GTE,
    TT_LTE,
    TT_BANG,
    TT_BANGEQ,
    TT_EQEQ,
    TT_DOT,
    TT_COLON,
    TT_SEMICOLON,
    TT_COMMA,
    TT_LPAREN,
    TT_RPAREN,
    TT_LBRACE,
    TT_RBRACE,
    TT_LBRACKET,
    TT_RBRACKET,
    TT_IDENT,
    TT_KEYWORD,
    TT_EOF,
    TT_NEWLINE
} TokenType;

struct Token {
    TokenType type;
    const char *start;
    size_t length;
    int line;
    int col;
    uint32_t intern_id;
    bool bool_value;
    int64_t int_value;
    double float_value;
};

struct Lexer {
    const char *source;
    size_t length;
    size_t pos;
    int line;
    int col;

    Token *tokens;
    size_t count;
    size_t capacity;

    Arena *arena;
    StringTable *strings;
    KeywordSet *keywords;
    Diagnostics *diags;
};

void lexer_init(Lexer *lexer, const char *source, size_t length,
                Arena *arena, StringTable *strings, KeywordSet *keywords,
                Diagnostics *diags);
void lexer_tokenise(Lexer *lexer);
const char *token_type_name(TokenType type);

#endif
