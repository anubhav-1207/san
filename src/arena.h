#ifndef SAN_ARENA_H
#define SAN_ARENA_H

#include "san.h"

struct Arena {
    struct ArenaBlock *blocks;
    size_t block_size;
    size_t used;
};

void arena_init(Arena *arena, size_t block_size);
void *arena_alloc(Arena *arena, size_t size);
void arena_reset(Arena *arena);
void arena_free(Arena *arena);

#endif
