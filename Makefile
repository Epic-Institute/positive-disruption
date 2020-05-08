all: lint test

flake8:
	flake8

black:
	black --check .

isort:
	isort -c

lint: flake8 black isort

test:
	pytest
