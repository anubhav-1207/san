#include "ast.h"

#include "arena.h"

#include <string.h>

AstNode *ast_new(Arena *arena, AstKind kind, int line, int col) {
    AstNode *node = arena_alloc(arena, sizeof(*node));
    if (node == NULL) {
        return NULL;
    }
    memset(node, 0, sizeof(*node));
    node->kind = kind;
    node->line = line;
    node->col = col;
    return node;
}

void ast_list_push(Arena *arena, AstList *list, AstNode *node) {
    if (list->count == list->capacity) {
        size_t capacity = list->capacity ? list->capacity * 2 : 8;
        AstNode **items = arena_alloc(arena, capacity * sizeof(*items));
        if (items == NULL) {
            return;
        }
        if (list->count > 0) {
            memcpy(items, list->items, list->count * sizeof(*items));
        }
        list->items = items;
        list->capacity = capacity;
    }
    list->items[list->count++] = node;
}

void token_list_push(Arena *arena, TokenList *list, const Token *token) {
    if (list->count == list->capacity) {
        size_t capacity = list->capacity ? list->capacity * 2 : 4;
        const Token **items = arena_alloc(arena, capacity * sizeof(*items));
        if (items == NULL) {
            return;
        }
        if (list->count > 0) {
            memcpy(items, list->items, list->count * sizeof(*items));
        }
        list->items = items;
        list->capacity = capacity;
    }
    list->items[list->count++] = token;
}

void ast_elif_push(Arena *arena, AstNode *node, AstNode *condition, AstList body) {
    if (node->as.if_node.elif_count == node->as.if_node.elif_capacity) {
        size_t capacity = node->as.if_node.elif_capacity ? node->as.if_node.elif_capacity * 2 : 2;
        AstElif *elifs = arena_alloc(arena, capacity * sizeof(*elifs));
        if (elifs == NULL) {
            return;
        }
        for (size_t i = 0; i < node->as.if_node.elif_count; i++) {
            elifs[i] = node->as.if_node.elifs[i];
        }
        node->as.if_node.elifs = elifs;
        node->as.if_node.elif_capacity = capacity;
    }
    node->as.if_node.elifs[node->as.if_node.elif_count].condition = condition;
    node->as.if_node.elifs[node->as.if_node.elif_count].body = body;
    node->as.if_node.elif_count++;
}

static void print_quoted(FILE *stream, const Token *token) {
    fputc('"', stream);
    if (token != NULL) {
        for (size_t i = 0; i < token->length; i++) {
            unsigned char ch = (unsigned char)token->start[i];
            if (ch == '"' || ch == '\\') {
                fputc('\\', stream);
                fputc((int)ch, stream);
            } else if (ch == '\n') {
                fputs("\\n", stream);
            } else if (ch == '\r') {
                fputs("\\r", stream);
            } else if (ch == '\t') {
                fputs("\\t", stream);
            } else if (ch < 0x20) {
                fprintf(stream, "\\u%04x", ch);
            } else {
                fputc((int)ch, stream);
            }
        }
    }
    fputc('"', stream);
}

static void print_list(FILE *stream, const AstList *list) {
    fputc('[', stream);
    for (size_t i = 0; i < list->count; i++) {
        if (i > 0) {
            fputc(' ', stream);
        }
        ast_print(stream, list->items[i]);
    }
    fputc(']', stream);
}

static void print_optional(FILE *stream, const AstNode *node) {
    if (node == NULL) {
        fputc('-', stream);
    } else {
        ast_print(stream, node);
    }
}

void ast_print(FILE *stream, const AstNode *node) {
    if (node == NULL) {
        fputs("(Error)", stream);
        return;
    }

    switch (node->kind) {
        case AST_PROGRAM:
            fputs("(Program ", stream);
            print_list(stream, &node->as.program.statements);
            fputc(')', stream);
            break;
        case AST_NUMBER:
            fputs("(Number ", stream);
            print_quoted(stream, node->as.number.token);
            fputc(')', stream);
            break;
        case AST_BOOL:
            fprintf(stream, "(Bool %s)", node->as.boolean.value ? "True" : "False");
            break;
        case AST_STRING:
            fputs("(String ", stream);
            print_quoted(stream, node->as.string.token);
            fputc(')', stream);
            break;
        case AST_NULL:
            fputs("(Null)", stream);
            break;
        case AST_UNARY:
            fputs("(Unary ", stream);
            print_quoted(stream, node->as.unary.op);
            fputc(' ', stream);
            ast_print(stream, node->as.unary.operand);
            fputc(')', stream);
            break;
        case AST_BINARY:
            fputs("(Binary ", stream);
            print_quoted(stream, node->as.binary.op);
            fputc(' ', stream);
            ast_print(stream, node->as.binary.left);
            fputc(' ', stream);
            ast_print(stream, node->as.binary.right);
            fputc(')', stream);
            break;
        case AST_VAR_ASSIGN:
            fputs("(VarAssign ", stream);
            print_quoted(stream, node->as.var_assign.name);
            fputs(node->as.var_assign.is_const ? " const " : " dec ", stream);
            ast_print(stream, node->as.var_assign.value);
            fputc(')', stream);
            break;
        case AST_VAR_REASSIGN:
            fputs("(VarReassign ", stream);
            print_quoted(stream, node->as.var_reassign.name);
            fputc(' ', stream);
            ast_print(stream, node->as.var_reassign.value);
            fputc(')', stream);
            break;
        case AST_VAR_ACCESS:
            fputs("(VarAccess ", stream);
            print_quoted(stream, node->as.var_access.name);
            fputc(')', stream);
            break;
        case AST_ARRAY:
            fputs("(Array ", stream);
            print_list(stream, &node->as.array.elements);
            fputc(')', stream);
            break;
        case AST_INDEX:
            fputs("(Index ", stream);
            print_quoted(stream, node->as.index.array);
            fputc(' ', stream);
            print_optional(stream, node->as.index.start);
            fputc(')', stream);
            break;
        case AST_SLICE:
            fputs("(Slice ", stream);
            print_quoted(stream, node->as.slice.array);
            fputc(' ', stream);
            print_optional(stream, node->as.slice.start);
            fputc(' ', stream);
            print_optional(stream, node->as.slice.end);
            fputc(' ', stream);
            print_optional(stream, node->as.slice.step);
            fputc(')', stream);
            break;
        case AST_TUPLE:
            fputs("(Tuple ", stream);
            print_list(stream, &node->as.tuple.elements);
            fputc(')', stream);
            break;
        case AST_CALL:
            fputs("(Call ", stream);
            print_quoted(stream, node->as.call.name);
            fputc(' ', stream);
            print_list(stream, &node->as.call.args);
            fputc(')', stream);
            break;
        case AST_FUNC_DEF:
            fputs("(FuncDef ", stream);
            print_quoted(stream, node->as.func_def.name);
            fputc(' ', stream);
            fputc('(', stream);
            for (size_t i = 0; i < node->as.func_def.params.count; i++) {
                if (i > 0) {
                    fputc(' ', stream);
                }
                print_quoted(stream, node->as.func_def.params.items[i]);
            }
            fputc(')', stream);
            fputc(' ', stream);
            print_list(stream, &node->as.func_def.body);
            fputc(')', stream);
            break;
        case AST_RETURN:
            fputs("(Return ", stream);
            print_optional(stream, node->as.ret.value);
            fputc(')', stream);
            break;
        case AST_BREAK:
            fputs("(Break)", stream);
            break;
        case AST_IF:
            fputs("(If ", stream);
            ast_print(stream, node->as.if_node.condition);
            fputc(' ', stream);
            print_list(stream, &node->as.if_node.body);
            fputc(' ', stream);
            fputc('[', stream);
            for (size_t i = 0; i < node->as.if_node.elif_count; i++) {
                if (i > 0) {
                    fputc(' ', stream);
                }
                fputs("(Elif ", stream);
                ast_print(stream, node->as.if_node.elifs[i].condition);
                fputc(' ', stream);
                print_list(stream, &node->as.if_node.elifs[i].body);
                fputc(')', stream);
            }
            fputs("] ", stream);
            if (node->as.if_node.has_else) {
                print_list(stream, &node->as.if_node.else_body);
            } else {
                fputs("[]", stream);
            }
            fputc(')', stream);
            break;
        case AST_WHILE:
            fputs("(While ", stream);
            ast_print(stream, node->as.while_node.condition);
            fputc(' ', stream);
            print_list(stream, &node->as.while_node.body);
            fputc(')', stream);
            break;
        case AST_FOR:
            fputs("(For ", stream);
            print_quoted(stream, node->as.for_node.variable);
            fputc(' ', stream);
            ast_print(stream, node->as.for_node.iterable);
            fputc(' ', stream);
            print_list(stream, &node->as.for_node.body);
            fputc(')', stream);
            break;
        case AST_SCAN:
            fputs("(Scan ", stream);
            print_quoted(stream, node->as.scan.variable);
            fputc(' ', stream);
            print_quoted(stream, node->as.scan.type_name);
            fputc(')', stream);
            break;
        case AST_USE:
            fputs("(Use ", stream);
            print_quoted(stream, node->as.use.library);
            fputc(')', stream);
            break;
        case AST_ERROR:
            fputs("(Error)", stream);
            break;
    }
}
