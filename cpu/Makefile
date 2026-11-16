PYTHON ?= python3

.PHONY: test bench hello sieve sort clean

test:
	$(PYTHON) tests/run_tests.py

bench:
	$(PYTHON) tools/bench.py

hello:
	$(PYTHON) tools/sanasm.py programs/hello.sasm --run

sieve:
	$(PYTHON) tools/sanasm.py programs/sieve.sasm --run

sort:
	$(PYTHON) tools/sanasm.py programs/bubble_sort.sasm --run

clean:
	rm -rf build/*.san build/*.lst
	find . -name __pycache__ -type d -prune -exec rm -rf {} +
