#include "arena.h"

#include <stdlib.h>

struct ArenaBlock {
    struct ArenaBlock *next;
    size_t capacity;
    unsigned char data[];
};

static size_t align_up(size_t value, size_t alignment) {
    return (value + alignment - 1) & ~(alignment - 1);
}

void arena_init(Arena *arena, size_t block_size) {
    arena->blocks = NULL;
    arena->block_size = block_size ? block_size : 4096;
    arena->used = 0;
}

void *arena_alloc(Arena *arena, size_t size) {
    if (size == 0) {
        size = 1;
    }
    size = align_up(size, 16);

    struct ArenaBlock *block = arena->blocks;
    if (block == NULL || arena->used + size > block->capacity) {
        size_t capacity = arena->block_size;
        if (size > capacity) {
            capacity = size;
        }
        block = malloc(sizeof(*block) + capacity);
        if (block == NULL) {
            return NULL;
        }
        block->next = arena->blocks;
        block->capacity = capacity;
        arena->blocks = block;
        arena->used = 0;
    }

    void *memory = block->data + arena->used;
    arena->used += size;
    return memory;
}

void arena_reset(Arena *arena) {
    arena->used = 0;
}

void arena_free(Arena *arena) {
    struct ArenaBlock *block = arena->blocks;
    while (block != NULL) {
        struct ArenaBlock *next = block->next;
        free(block);
        block = next;
    }
    arena->blocks = NULL;
    arena->used = 0;
}
