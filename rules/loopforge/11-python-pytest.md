# Python Pytest Rule

## Detection

Possible indicators:

- `pyproject.toml`
- `requirements.txt`
- `pytest.ini`
- `setup.cfg`
- `setup.py`

## Verification Intent

Preferred verification order:

1. `pytest`
2. `python -m pytest`
3. `python3 -m pytest`
4. `python -m compileall .`
5. `python3 -m compileall .`

## Current Status

This rule is documentation-first in the current milestone. Detection support exists in the runner, but verification execution is not yet implemented.
