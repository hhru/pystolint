import tempfile
from collections.abc import Generator
from pathlib import Path

import pytest

from pystolint.ruff.ruff_check import run_ruff_check, run_ruff_format_check
from pystolint.util.git import default_base_branch_name


@pytest.fixture
def ruff_config() -> Generator[str]:
    with tempfile.TemporaryDirectory() as tmpdir:
        config_path = Path(tmpdir) / 'ruff.toml'
        config_path.write_text(
            '[lint]\n'
            'select = ["E4", "E7", "E9", "F"]\n'
            '\n'
            '[format]\n'
            'quote-style = "single"\n'
            'indent-style = "space"\n'
            'line-ending = "auto"\n'
        )
        yield str(config_path)


@pytest.fixture
def unformatted_file() -> Generator[str]:
    with tempfile.TemporaryDirectory() as tmpdir:
        file_path = Path(tmpdir) / 'test.py'
        # Create an intentionally poorly formatted Python file
        file_path.write_text('def   badly_formatted  (  x  ) :\n    return   x    +  42')
        yield str(file_path)


@pytest.fixture
def file_with_lint_errors() -> Generator[str]:
    with tempfile.TemporaryDirectory() as tmpdir:
        file_path = Path(tmpdir) / 'test_lint.py'
        # Create a file with various lint errors
        file_path.write_text('def unused_arg(x):\n    return 42\n\ndef undefined_var():\n    return y + 1\n')
        yield str(file_path)


def test_run_ruff_format_check_needs_formatting(unformatted_file: str, ruff_config: str) -> None:
    result = run_ruff_format_check(ruff_config, [unformatted_file])
    assert len(result.items) == 1
    assert result.items[0].file_path == unformatted_file
    assert result.items[0].message == 'should be reformatted'


def test_run_ruff_format_check_properly_formatted(ruff_config: str) -> None:
    with tempfile.TemporaryDirectory() as tmpdir:
        file_path = Path(tmpdir) / 'test.py'
        # Create a properly formatted file
        file_path.write_text('def properly_formatted(x):\n    return x + 42\n')
        result = run_ruff_format_check(ruff_config, [str(file_path)])
        assert len(result.items) == 0


def test_run_ruff_check_lint_errors(file_with_lint_errors: str, ruff_config: str) -> None:
    result = run_ruff_check(ruff_config, [file_with_lint_errors])
    assert len(result.items) > 0

    # Convert results to a list of (code, message) tuples for easier testing
    error_codes = {result.message.split(':')[0] for result in result.items}

    # Should find undefined name 'y'
    assert 'F821' in error_codes


def test_run_ruff_check_clean_file(ruff_config: str) -> None:
    with tempfile.TemporaryDirectory() as tmpdir:
        file_path = Path(tmpdir) / 'test.py'
        # Create a clean file with no lint errors
        file_path.write_text('def clean_function(x):\n    return x + 42\n')
        result = run_ruff_check(ruff_config, [str(file_path)])
        assert len(result.items) == 0


def test_run_ruff_check_syntax_error(ruff_config: str) -> None:
    with tempfile.TemporaryDirectory() as tmpdir:
        file_path = Path(tmpdir) / 'invalid.py'
        # Create a file with invalid Python syntax
        file_path.write_text('def invalid_syntax(:\n    return 42')

        result = run_ruff_check(ruff_config, [str(file_path)])
        assert len(result.items) > 0
        assert any('SyntaxError' in r.message for r in result.items)  # E999 is syntax error code


def test_run_ruff_check_multiple_files(ruff_config: str) -> None:
    with tempfile.TemporaryDirectory() as tmpdir:
        # Create one clean file and one with errors
        clean_file = Path(tmpdir) / 'clean.py'
        error_file = Path(tmpdir) / 'error.py'

        clean_file.write_text('def clean(x):\n    return x + 1\n')
        error_file.write_text('def error():\n    return y\n')  # undefined y

        result = run_ruff_check(ruff_config, [str(clean_file), str(error_file)])
        assert len(result.items) == 1
        assert result.items[0].file_path.endswith(str(error_file))
        assert 'F821' in result.items[0].message  # undefined name error


def test_run_ruff_check_with_diff_mode(ruff_config: str, monkeypatch: pytest.MonkeyPatch) -> None:
    with tempfile.TemporaryDirectory() as tmpdir:
        file_path = Path(tmpdir) / 'test.py'
        file_path.write_text('def error():\n    return y\n')  # undefined y

        # Mock git changed lines to simulate diff mode
        def mock_git_changed_lines(base_branch_name: str = default_base_branch_name) -> dict[str, set[int]]:
            return {str(file_path): {2}}  # Only line 2 was changed

        monkeypatch.setattr('pystolint.ruff.ruff_check.get_git_changed_lines', mock_git_changed_lines)

        # Run check in diff mode
        result = run_ruff_check(ruff_config, [str(file_path)], diff=True)
        assert len(result.items) == 1
        assert result.items[0].line == 2  # Error on line 2
        assert 'F821' in result.items[0].message  # undefined name error
