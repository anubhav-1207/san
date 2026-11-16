#include "table.h"

#include "arena.h"

#include <stdlib.h>
#include <string.h>

static uint64_t hash_bytes(const char *text, size_t length) {
    uint64_t hash = 1469598103934665603ULL;
    for (size_t i = 0; i < length; i++) {
        hash ^= (unsigned char)text[i];
        hash *= 1099511628211ULL;
    }
    return hash;
}

static size_t find_slot(const StringTable *table, const char *text, size_t length) {
    size_t mask = table->capacity - 1;
    size_t slot = (size_t)hash_bytes(text, length) & mask;
    while (table->buckets[slot] != 0) {
        const struct StringTableEntry *entry = &table->entries[table->buckets[slot] - 1];
        if (entry->length == length && memcmp(entry->text, text, length) == 0) {
            return slot;
        }
        slot = (slot + 1) & mask;
    }
    return slot;
}

static void rehash(StringTable *table, size_t capacity) {
    size_t *buckets = calloc(capacity, sizeof(*buckets));
    if (buckets == NULL) {
        return;
    }
    size_t mask = capacity - 1;
    for (size_t i = 0; i < table->count; i++) {
        const struct StringTableEntry *entry = &table->entries[i];
        size_t slot = (size_t)hash_bytes(entry->text, entry->length) & mask;
        while (buckets[slot] != 0) {
            slot = (slot + 1) & mask;
        }
        buckets[slot] = i + 1;
    }
    free(table->buckets);
    table->buckets = buckets;
    table->capacity = capacity;
}

void strtab_init(StringTable *table, Arena *arena, size_t capacity) {
    if (capacity < 16) {
        capacity = 16;
    }
    while ((capacity & (capacity - 1)) != 0) {
        capacity++;
    }
    table->arena = arena;
    table->entries = NULL;
    table->count = 0;
    table->capacity = 0;
    table->buckets = NULL;
    rehash(table, capacity);
}

void strtab_free(StringTable *table) {
    free(table->entries);
    free(table->buckets);
    table->entries = NULL;
    table->buckets = NULL;
    table->count = 0;
    table->capacity = 0;
}

uint32_t strtab_intern(StringTable *table, const char *text, size_t length) {
    size_t slot = find_slot(table, text, length);
    if (table->buckets[slot] != 0) {
        return table->entries[table->buckets[slot] - 1].id;
    }

    if ((table->count + 1) * 10 >= table->capacity * 7) {
        rehash(table, table->capacity * 2);
        slot = find_slot(table, text, length);
    }

    char *copy = arena_alloc(table->arena, length + 1);
    if (copy == NULL) {
        return 0;
    }
    memcpy(copy, text, length);
    copy[length] = '\0';

    struct StringTableEntry *entries = realloc(table->entries, (table->count + 1) * sizeof(*entries));
    if (entries == NULL) {
        return 0;
    }
    table->entries = entries;

    uint32_t id = (uint32_t)(table->count + 1);
    table->entries[table->count].text = copy;
    table->entries[table->count].length = length;
    table->entries[table->count].id = id;
    table->buckets[slot] = table->count + 1;
    table->count++;
    return id;
}

const char *strtab_text(const StringTable *table, uint32_t id) {
    if (id == 0 || id > table->count) {
        return "";
    }
    return table->entries[id - 1].text;
}

size_t strtab_length(const StringTable *table, uint32_t id) {
    if (id == 0 || id > table->count) {
        return 0;
    }
    return table->entries[id - 1].length;
}

static const char *const KEYWORDS[] = {
    "dec", "const", "flux", "arr", "func", "return",
    "if", "else", "elif", "while", "loop", "for", "in",
    "break", "skip", "Null", "use", "scan", "try", "catch", "drop",
    "int", "float", "str", "bool", "div"
};

void kw_init(KeywordSet *set, StringTable *table) {
    size_t count = sizeof(KEYWORDS) / sizeof(KEYWORDS[0]);
    set->ids = malloc(count * sizeof(*set->ids));
    set->count = 0;
    if (set->ids == NULL) {
        return;
    }
    for (size_t i = 0; i < count; i++) {
        set->ids[set->count++] = strtab_intern(table, KEYWORDS[i], strlen(KEYWORDS[i]));
    }
}

bool kw_contains(const KeywordSet *set, uint32_t id) {
    for (size_t i = 0; i < set->count; i++) {
        if (set->ids[i] == id) {
            return true;
        }
    }
    return false;
}
