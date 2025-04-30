import tempfile
from collections.abc import Generator
from pathlib import Path

import pytest

from pystolint.ruff.ruff_format import run_ruff_format


@pytest.fixture
def unformatted_file() -> Generator[str]:
    with tempfile.TemporaryDirectory() as tmpdir:
        file_path = Path(tmpdir) / 'test.py'
        # Create an intentionally poorly formatted Python file
        file_path.write_text('def   badly_formatted  (  x  ) :\n    return   x    +  42')
        yield str(file_path)


@pytest.fixture
def ruff_config() -> Generator[str]:
    with tempfile.TemporaryDirectory() as tmpdir:
        config_path = Path(tmpdir) / 'ruff.toml'
        config_path.write_text('[format]\nquote-style = "single"\nindent-style = "space"\nline-ending = "auto"\n')
        yield str(config_path)


def test_run_ruff_format(unformatted_file: str, ruff_config: str) -> None:
    # Run the formatter
    run_ruff_format(ruff_config, [unformatted_file])

    # Read the formatted content
    formatted_content = Path(unformatted_file).read_text()

    # Expected formatting based on ruff's default style
    expected = 'def badly_formatted(x):\n    return x + 42\n'

    assert formatted_content == expected


def test_run_ruff_format_multiple_files(ruff_config: str) -> None:
    with tempfile.TemporaryDirectory() as tmpdir:
        # Create multiple unformatted files
        file1 = Path(tmpdir) / 'test1.py'
        file2 = Path(tmpdir) / 'test2.py'

        file1.write_text('def  func1(   ):\n   return    1')
        file2.write_text('def  func2(   ):\n   return    2')

        files = [str(file1), str(file2)]
        run_ruff_format(ruff_config, files)

        # Check formatting of both files
        assert file1.read_text() == 'def func1():\n    return 1\n'
        assert file2.read_text() == 'def func2():\n    return 2\n'


def test_run_ruff_format_syntax_error(ruff_config: str) -> None:
    with tempfile.TemporaryDirectory() as tmpdir:
        file_path = Path(tmpdir) / 'invalid.py'
        # Create a file with invalid Python syntax
        file_path.write_text('def invalid_syntax(:\n    return 42')

        with pytest.raises(SystemExit) as exc_info:
            run_ruff_format(ruff_config, [str(file_path)])

        assert isinstance(exc_info.value.code, int)
        assert exc_info.value.code > 1  # ruff returns code > 1 for errors
