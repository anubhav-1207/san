#include "error.h"

#include <stdarg.h>
#include <stdlib.h>
#include <string.h>

typedef struct {
    const char *code;
    const char *class_name;
    Severity severity;
    Security security;
} CodeInfo;

static const CodeInfo CODE_INFO[ERR_COUNT] = {
    [ERR_LEX001]     = {"LEX001",   "source.fatal",     SEVERITY_FATAL,   SECURITY_HIGH},
    [ERR_LEX002]     = {"LEX002",   "source.recursive", SEVERITY_ERROR,   SECURITY_MEDIUM},
    [ERR_LEX003]     = {"LEX003",   "source.fatal",     SEVERITY_ERROR,   SECURITY_MEDIUM},
    [ERR_LEX004]     = {"LEX004",   "source.recursive", SEVERITY_ERROR,   SECURITY_LOW},
    [ERR_LEX005]     = {"LEX005",   "source.recursive", SEVERITY_ERROR,   SECURITY_LOW},
    [ERR_PAR001]     = {"PAR001",   "source.fatal",     SEVERITY_FATAL,   SECURITY_HIGH},
    [ERR_PAR002]     = {"PAR002",   "source.fatal",     SEVERITY_ERROR,   SECURITY_LOW},
    [ERR_PAR003]     = {"PAR003",   "source.recursive", SEVERITY_ERROR,   SECURITY_MEDIUM},
    [ERR_PAR004]     = {"PAR004",   "source.fatal",     SEVERITY_ERROR,   SECURITY_MEDIUM},
    [ERR_PAR005]     = {"PAR005",   "source.fatal",     SEVERITY_ERROR,   SECURITY_MEDIUM},
    [ERR_INTRPTR001] = {"INTRPTR001", "source.fatal",     SEVERITY_ERROR,   SECURITY_MEDIUM},
    [ERR_INTRPTR002] = {"INTRPTR002", "source.fatal",     SEVERITY_FATAL,   SECURITY_HIGH},
    [ERR_INTRPTR003] = {"INTRPTR003", "source.fatal",     SEVERITY_FATAL,   SECURITY_HIGH},
    [ERR_INTRPTR004] = {"INTRPTR004", "source.fatal",     SEVERITY_ERROR,   SECURITY_MEDIUM},
    [ERR_INTRPTR005] = {"INTRPTR005", "source.recursive", SEVERITY_FATAL,   SECURITY_HIGH},
    [ERR_INTRPTR006] = {"INTRPTR006", "source.fatal",     SEVERITY_ERROR,   SECURITY_MEDIUM},
    [ERR_INTRPTR007] = {"INTRPTR007", "source.fatal",     SEVERITY_ERROR,   SECURITY_HIGH}
};

static const char *const SEVERITY_NAMES[] = {"FATAL", "ERROR", "WARNING", "INFO"};
static const char *const SECURITY_NAMES[] = {"NONE", "LOW", "MEDIUM", "HIGH", "CRITICAL"};
static const char *const PHASE_NAMES[] = {"lexer", "parser", "interpreter"};

void diags_init(Diagnostics *diags) {
    diags->items = NULL;
    diags->count = 0;
    diags->capacity = 0;
}

void diags_free(Diagnostics *diags) {
    free(diags->items);
    diags->items = NULL;
    diags->count = 0;
    diags->capacity = 0;
}

static void add_impl(Diagnostics *diags, ErrorCode code, SanPhase phase,
                     const char *class_name, int line, int col,
                     const char *format, va_list args) {
    if (diags->count == diags->capacity) {
        size_t capacity = diags->capacity ? diags->capacity * 2 : 8;
        Diagnostic *items = realloc(diags->items, capacity * sizeof(*items));
        if (items == NULL) {
            return;
        }
        diags->items = items;
        diags->capacity = capacity;
    }

    Diagnostic *diag = &diags->items[diags->count++];
    diag->code = code;
    diag->phase = phase;
    diag->class_name = class_name;
    diag->line = line;
    diag->col = col;
    vsnprintf(diag->message, sizeof(diag->message), format, args);
}

void diags_add(Diagnostics *diags, ErrorCode code, SanPhase phase,
               int line, int col, const char *format, ...) {
    va_list args;
    va_start(args, format);
    add_impl(diags, code, phase, NULL, line, col, format, args);
    va_end(args);
}

void diags_add_as(Diagnostics *diags, ErrorCode code, SanPhase phase,
                  const char *class_name, int line, int col,
                  const char *format, ...) {
    va_list args;
    va_start(args, format);
    add_impl(diags, code, phase, class_name, line, col, format, args);
    va_end(args);
}

bool diags_has_errors(const Diagnostics *diags) {
    for (size_t i = 0; i < diags->count; i++) {
        Severity severity = CODE_INFO[diags->items[i].code].severity;
        if (severity == SEVERITY_FATAL || severity == SEVERITY_ERROR) {
            return true;
        }
    }
    return false;
}

static int compare_diagnostics(const void *left, const void *right) {
    const Diagnostic *a = left;
    const Diagnostic *b = right;
    if (a->phase != b->phase) {
        return a->phase < b->phase ? -1 : 1;
    }
    if (a->line != b->line) {
        return a->line < b->line ? -1 : 1;
    }
    if (a->col != b->col) {
        return a->col < b->col ? -1 : 1;
    }
    return a->code < b->code ? -1 : (a->code > b->code ? 1 : 0);
}

void diags_print(const Diagnostics *diags, FILE *stream) {
    if (diags->count == 0) {
        return;
    }
    Diagnostic *sorted = malloc(diags->count * sizeof(*sorted));
    if (sorted == NULL) {
        return;
    }
    memcpy(sorted, diags->items, diags->count * sizeof(*sorted));
    qsort(sorted, diags->count, sizeof(*sorted), compare_diagnostics);

    for (size_t i = 0; i < diags->count; i++) {
        const Diagnostic *diag = &sorted[i];
        const CodeInfo *info = &CODE_INFO[diag->code];
        fprintf(stream, "[%s | SECURITY: %s] %s:: %s ---> %s exited with error[#%s], line:col %d:%d\n",
                SEVERITY_NAMES[info->severity], SECURITY_NAMES[info->security],
                diag->class_name ? diag->class_name : info->class_name,
                diag->message, PHASE_NAMES[diag->phase],
                info->code, diag->line, diag->col);
    }
    free(sorted);
}
