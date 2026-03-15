PYTHON ?= python
COVERAGE_FAIL_UNDER ?= 70

.PHONY: install format lint typecheck test test-ci ci clean

install:
	$(PYTHON) -m pip install -U pip
	$(PYTHON) -m pip install -e .[dev]

format:
	$(PYTHON) -m ruff format src tests

lint:
	$(PYTHON) -m ruff check src tests

typecheck:
	$(PYTHON) -m mypy src

test:
	$(PYTHON) -m pytest

test-ci:
	$(PYTHON) -m pytest --cov-report=xml --junitxml=pytest.xml --cov-fail-under=$(COVERAGE_FAIL_UNDER)

ci: lint typecheck test-ci

clean:
	$(PYTHON) -c "import shutil, pathlib; [shutil.rmtree(p, ignore_errors=True) for p in ['.pytest_cache','.mypy_cache','.ruff_cache','htmlcov','build','dist']]; [p.unlink() for p in pathlib.Path('.').glob('.coverage*') if p.is_file()]"
