install:
	pip install -e ".[test]"

run:
	uvicorn app.main:app --reload

test:
	pytest -q
