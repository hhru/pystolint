import tempfile
from collections.abc import Generator
from pathlib import Path

import pytest

from pystolint.mypy.mypy_check import run_mypy_check
from pystolint.util.git import default_base_branch_name


@pytest.fixture
def mypy_config() -> Generator[str]:
    with tempfile.NamedTemporaryFile(mode='w', suffix='.toml') as tmp_config:
        # Basic mypy configuration that enforces type checking
        config_content = (
            '[mypy]\n'
            'warn_redundant_casts = true\n'
            'warn_unused_ignores = true\n'
            'disallow_untyped_defs = true\n'
            'check_untyped_defs = true\n'
            'strict = true'
        )
        tmp_config.write(config_content)
        tmp_config.flush()
        yield tmp_config.name


@pytest.fixture
def type_error_file() -> Generator[str]:
    with tempfile.TemporaryDirectory() as tmpdir:
        file_path = Path(tmpdir) / 'test_type_error.py'
        # Create a file with intentional type errors
        file_content = (
            'def add(x: int, y: str) -> int:\n'
            '    return x + y  # Type error: cannot add int and str\n'
            '\n'
            'typed_var: int = "not an integer"  # Type error: incompatible types'
        )
        file_path.write_text(file_content)
        yield str(file_path)


def test_run_mypy_check_finds_errors(mypy_config: str, type_error_file: str) -> None:
    # Run mypy check
    result = run_mypy_check(mypy_config, [type_error_file])

    # Verify that mypy found the expected type errors
    assert len(result.items) >= 2  # We expect at least 2 errors

    # Check for specific errors we know should be present
    expected_errors = {
        # Error for adding int and str
        (2, 'Unsupported operand types for + ("int" and "str")'),
        # Error for invalid type assignment
        (4, 'Incompatible types in assignment (expression has type "str", variable has type "int")'),
    }

    # Check that all expected errors are found
    # Note: The exact error messages might vary slightly with mypy versions
    # so we check that each expected line has some error
    assert all(any(r.line == expected_line for r in result.items) for expected_line, _ in expected_errors)


def test_run_mypy_check_clean_file(mypy_config: str) -> None:
    with tempfile.TemporaryDirectory() as tmpdir:
        file_path = Path(tmpdir) / 'test_clean.py'
        # Create a file with no type errors
        file_content = 'def add(x: int, y: int) -> int:\n    return x + y\n\ntyped_var: str = "this is fine"'
        file_path.write_text(file_content)

        result = run_mypy_check(mypy_config, [str(file_path)])
        assert len(result.items) == 0, 'Expected no type errors in clean file'


def test_run_mypy_check_with_diff_mode(mypy_config: str, type_error_file: str, monkeypatch: pytest.MonkeyPatch) -> None:
    # Mock get_git_changed_lines to simulate diff mode
    def mock_get_changed_lines(base_branch_name: str = default_base_branch_name) -> dict[str, set[int]]:
        return {
            type_error_file: {2, 4}  # Only lines 2 and 4 are "changed"
        }

    monkeypatch.setattr('pystolint.mypy.mypy_check.get_git_changed_lines', mock_get_changed_lines)

    result = run_mypy_check(mypy_config, [type_error_file], diff=True)

    # We should only get errors from the "changed" lines
    assert all(r.line in {2, 4} for r in result.items)
    assert len(result.items) == 2
