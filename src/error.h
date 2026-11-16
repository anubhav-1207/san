#ifndef SAN_ERROR_H
#define SAN_ERROR_H

#include "san.h"

#include <stdio.h>

typedef enum {
    SAN_PHASE_LEXER = 0,
    SAN_PHASE_PARSER = 1,
    SAN_PHASE_INTERPRETER = 2
} SanPhase;

typedef enum {
    SEVERITY_FATAL = 0,
    SEVERITY_ERROR = 1,
    SEVERITY_WARNING = 2,
    SEVERITY_INFO = 3
} Severity;

typedef enum {
    SECURITY_NONE = 0,
    SECURITY_LOW,
    SECURITY_MEDIUM,
    SECURITY_HIGH,
    SECURITY_CRITICAL
} Security;

typedef enum {
    ERR_LEX001 = 0,
    ERR_LEX002,
    ERR_LEX003,
    ERR_LEX004,
    ERR_LEX005,
    ERR_PAR001,
    ERR_PAR002,
    ERR_PAR003,
    ERR_PAR004,
    ERR_PAR005,
    ERR_INTRPTR001,
    ERR_INTRPTR002,
    ERR_INTRPTR003,
    ERR_INTRPTR004,
    ERR_INTRPTR005,
    ERR_INTRPTR006,
    ERR_INTRPTR007,
    ERR_COUNT
} ErrorCode;

typedef struct {
    ErrorCode code;
    SanPhase phase;
    const char *class_name;
    int line;
    int col;
    char message[256];
} Diagnostic;

struct Diagnostics {
    Diagnostic *items;
    size_t count;
    size_t capacity;
};

void diags_init(Diagnostics *diags);
void diags_free(Diagnostics *diags);
void diags_add(Diagnostics *diags, ErrorCode code, SanPhase phase,
               int line, int col, const char *format, ...);
void diags_add_as(Diagnostics *diags, ErrorCode code, SanPhase phase,
                  const char *class_name, int line, int col,
                  const char *format, ...);
bool diags_has_errors(const Diagnostics *diags);
void diags_print(const Diagnostics *diags, FILE *stream);

#endif
