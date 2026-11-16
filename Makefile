CC ?= cc
CFLAGS ?= -std=c11 -O2 -Wall -Wextra -Wpedantic
PREFIX ?= /usr/local
DESTDIR ?=

SOURCES = src/main.c src/error.c src/arena.c src/table.c src/lexer.c src/ast.c src/parser.c
OBJECTS = $(SOURCES:src/%.c=build/%.o)

.PHONY: all check install clean

all: san

san: $(OBJECTS)
	$(CC) $(CFLAGS) -o $@ $(OBJECTS) -lm

build/%.o: src/%.c
	mkdir -p build
	$(CC) $(CFLAGS) -c -o $@ $<

check: san
	python3 tests/lexer_diff.py
	python3 tests/parser_diff.py

install: san
	install -d $(DESTDIR)$(PREFIX)/bin
	install -m 0755 san $(DESTDIR)$(PREFIX)/bin/san

clean:
	rm -rf build san
