formatting:
	@python -m black . --line-length=120

check-formatting:
	@python -m black . --check --line-length=120

diff-formatting:
	@python -m black . --diff --line-length=120

check-code:
	@python -m flake8 src

audit: check-formatting check-code