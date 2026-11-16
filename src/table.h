#ifndef SAN_TABLE_H
#define SAN_TABLE_H

#include "san.h"

struct StringTableEntry {
    const char *text;
    size_t length;
    uint32_t id;
};

struct StringTable {
    struct StringTableEntry *entries;
    size_t *buckets;
    size_t capacity;
    size_t count;
    Arena *arena;
};

struct KeywordSet {
    uint32_t *ids;
    size_t count;
};

void strtab_init(StringTable *table, Arena *arena, size_t capacity);
void strtab_free(StringTable *table);
uint32_t strtab_intern(StringTable *table, const char *text, size_t length);
const char *strtab_text(const StringTable *table, uint32_t id);
size_t strtab_length(const StringTable *table, uint32_t id);

void kw_init(KeywordSet *set, StringTable *table);
bool kw_contains(const KeywordSet *set, uint32_t id);

#endif
