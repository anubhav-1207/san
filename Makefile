CC ?= cc
CFLAGS ?= -std=c11 -O2 -Wall -Wextra -Wpedantic
PREFIX ?= /usr/local
DESTDIR ?=

SOURCES = src/main.c src/error.c src/arena.c src/table.c src/lexer.c src/ast.c src/parser.c \
          src/value.c src/env.c src/interpreter.c \
          src/stdlib/registry.c src/stdlib/builtins.c src/stdlib/arrays.c \
          src/stdlib/strings.c src/stdlib/mathlib.c src/stdlib/random.c src/stdlib/timelib.c
OBJECTS = $(SOURCES:src/%.c=build/%.o)

.PHONY: all check install clean

all: san

san: $(OBJECTS)
	$(CC) $(CFLAGS) -o $@ $(OBJECTS) -lm

build/%.o: src/%.c
	mkdir -p $(dir $@)
	$(CC) $(CFLAGS) -c -o $@ $<

check: san
	python3 tests/lexer_diff.py
	python3 tests/parser_diff.py
	python3 tests/interpreter_diff.py

install: san
	install -d $(DESTDIR)$(PREFIX)/bin
	install -m 0755 san $(DESTDIR)$(PREFIX)/bin/san

clean:
	rm -rf build san
