#include "san.h"

#include "arena.h"
#include "error.h"
#include "lexer.h"
#include "table.h"

#include <stdio.h>
#include <stdlib.h>
#include <string.h>

static void print_usage(FILE *stream) {
    fprintf(stream,
            "Usage:\n"
            "  san <file.san>                  tokenise the file\n"
            "  san <file.san> explicit         tokenise and dump tokens\n"
            "  san --tokens <file.san>         same as 'explicit'\n"
            "  san --help                      show this help\n"
            "  san --version                   show the version\n"
            "\n"
            "Diagnostics are collected and printed at the end:\n"
            "  [SEVERITY | SECURITY: LEVEL] source.<class>:: message ---> <phase> exited with error[#CODE], line:col L:C\n"
            "  severity: FATAL > ERROR > WARNING > INFO\n"
            "  security: CRITICAL > HIGH > MEDIUM > LOW > NONE\n"
            "\n"
            "Current build stage: lexer only.\n");
}

static char *read_file(const char *path, size_t *length) {
    FILE *file = fopen(path, "rb");
    if (file == NULL) {
        return NULL;
    }
    if (fseek(file, 0, SEEK_END) != 0) {
        fclose(file);
        return NULL;
    }
    long size = ftell(file);
    if (size < 0) {
        fclose(file);
        return NULL;
    }
    rewind(file);

    char *buffer = malloc((size_t)size + 1);
    if (buffer == NULL) {
        fclose(file);
        return NULL;
    }
    size_t read = fread(buffer, 1, (size_t)size, file);
    fclose(file);
    buffer[read] = '\0';
    *length = read;
    return buffer;
}

static void print_token(const Token *token) {
    printf("Token(%s", token_type_name(token->type));
    if (token->type != TT_EOF && token->type != TT_NEWLINE) {
        if (token->type == TT_BOOL) {
            printf(":%s", token->bool_value ? "True" : "False");
        } else if (token->length > 0) {
            printf(":%.*s", (int)token->length, token->start);
        }
    }
    printf(" -> line - %d, col - %d)\n", token->line, token->col);
}

int main(int argc, char **argv) {
    bool dump_tokens = false;
    const char *path = NULL;

    for (int i = 1; i < argc; i++) {
        const char *arg = argv[i];
        if (strcmp(arg, "--help") == 0 || strcmp(arg, "-h") == 0) {
            print_usage(stdout);
            return 0;
        }
        if (strcmp(arg, "--version") == 0) {
            printf("san %s\n", SAN_VERSION);
            return 0;
        }
        if (strcmp(arg, "--tokens") == 0 || strcmp(arg, "--explicit") == 0 ||
            strcmp(arg, "explicit") == 0) {
            dump_tokens = true;
        } else if (path == NULL) {
            path = arg;
        } else {
            fprintf(stderr, "Error: unexpected argument '%s'\n", arg);
            print_usage(stderr);
            return 2;
        }
    }

    if (path == NULL) {
        print_usage(stderr);
        return 2;
    }

    size_t path_length = strlen(path);
    if (path_length < 4 || strcmp(path + path_length - 4, ".san") != 0) {
        fprintf(stderr, "Error: File must have .san extension\n");
        return 1;
    }

    size_t length = 0;
    char *source = read_file(path, &length);
    if (source == NULL) {
        fprintf(stderr, "Error: File '%s' not found\n", path);
        return 1;
    }

    Arena arena;
    StringTable strings;
    KeywordSet keywords;
    Diagnostics diags;
    Lexer lexer;

    arena_init(&arena, 8192);
    strtab_init(&strings, &arena, 128);
    kw_init(&keywords, &strings);
    diags_init(&diags);
    lexer_init(&lexer, source, length, &arena, &strings, &keywords, &diags);

    lexer_tokenise(&lexer);

    if (dump_tokens) {
        for (size_t i = 0; i < lexer.count; i++) {
            print_token(&lexer.tokens[i]);
        }
    }

    diags_print(&diags, stderr);
    int status = diags_has_errors(&diags) ? 1 : 0;

    diags_free(&diags);
    free(keywords.ids);
    strtab_free(&strings);
    arena_free(&arena);
    free(source);
    return status;
}
