.DEFAULT_GOAL := run

.PHONY: clean install run all

clean:
	find src | grep -E "__pycache__" | xargs rm -rf
	rm -rf output src/parser.out src/parsetab.py
	rm -rf ami
	rm -f *.ami

install:
	pip install -r requirements.txt

run:
	mkdir -p output
	bash ./test.sh
