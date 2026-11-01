# Agents Lab

Requires Python 3.14+, [uv](https://docs.astral.sh/uv/) with `uv audit`
support, and [Task](https://taskfile.dev/).

Set up the development environment:

```sh
task init:dev
```

This creates `.venv` if needed and installs the project and development
dependencies from `uv.lock`. It is safe to run again to sync an existing
environment. Task commands use the environment automatically; manual
activation is optional (`source .venv/bin/activate`).

Before starting trainee work, check the connection to the OpenAPI model:

```sh
task run:module_00
```

This check is required before continuing with the trainee exercises. The task
loads environment variables from `.env`, so configure the required model
connection settings there first.

Run all checks:

```sh
task check
```

Run individual tasks:

```sh
task ty          # Type checking
task ruff:check  # Lint and formatting checks
task ruff:fix    # Apply safe automatic lint fixes
task uv:audit    # Dependency vulnerability audit (requires network access)
task --list     # List available tasks
```

The Python check tasks use `uv run --group dev` to install and run the project's
development tools. `task check` stops at the first failed check and does not apply
automatic fixes.

Run tests or generate coverage reports:

```sh
task pytest           # Tests with terminal coverage and missing lines
task pytest:coverage  # Also write HTML and XML coverage reports
task pytest -- -k test_name
```

Add tests under `tests/` with filenames matching `test_*.py` or `*_test.py`.
Pytest uses strict configuration and marker validation, and importlib
import mode. Coverage measures lines and branches in `agents_lab`.
`task pytest` prints a terminal summary with missing lines;
`task pytest:coverage` also writes `htmlcov/index.html` and `coverage.xml`. No minimum
coverage threshold is enforced. Generated reports are ignored by Git.

Ruff lint, formatter, pytest, and coverage settings live in `pyproject.toml`.
Ruff checks common Python errors, import ordering, bugbear rules, and Python
upgrade rules. Coverage uses
[pytest-cov](https://pytest-cov.readthedocs.io/en/latest/config.html).

Update packages and pre-commit hooks together:

```sh
task update
```

This updates dependencies to the latest versions allowed by `pyproject.toml`,
syncs the development environment, and then updates pinned hook versions in
`.pre-commit-config.yaml`. Both update steps require network access.
To run either step separately:

```sh
task packages:update
task pre-commit:update
```

Install the Git hook once per clone:

```sh
task pre-commit:install
```

Pre-commit uses the official
[ty](https://github.com/astral-sh/ty-pre-commit),
[Ruff](https://github.com/astral-sh/ruff-pre-commit), and
[uv](https://github.com/astral-sh/uv-pre-commit) hook repositories, pinned to
explicit versions and installed in environments managed by pre-commit.
These hooks check the whole project before every commit, do not apply fixes,
and require network access for the vulnerability audit and initial installation.
Hook versions are pinned separately from `uv.lock`; update them with
`task pre-commit:update`.
