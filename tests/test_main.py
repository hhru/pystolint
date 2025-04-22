from io import StringIO
from unittest.mock import patch

import pytest

from pystolint.main import main, process_paths


def test_main_check_mode() -> None:
    with (
        patch('sys.argv', ['pystolint', 'check', '/some_file.py']),
        patch('pystolint.main.check_with_stdout') as mock_check,
    ):
        main()
        mock_check.assert_called_once_with(
            ['/some_file.py'],
            base_branch_name_provided=None,
            diff=False,
            local_toml_path_provided=None,
            base_toml_path_provided=None,
        )


def test_main_format_mode() -> None:
    with (
        patch('sys.argv', ['pystolint', 'format', '/some_file.py']),
        patch('pystolint.main.format_with_stdout') as mock_format,
        patch('sys.stdout', new=StringIO()),
    ):
        main()
        mock_format.assert_called_once_with(
            ['/some_file.py'], local_toml_path_provided=None, base_toml_path_provided=None
        )


def test_main_with_diff_flag() -> None:
    with (
        patch('sys.argv', ['pystolint', 'check', '--diff']),
        patch('pystolint.main.check_with_stdout') as mock_check,
        patch('pystolint.main.process_paths') as mock_process_paths,
        patch('sys.stdout', new=StringIO()),
    ):
        mock_process_paths.return_value = ['changed_file.py']
        main()
        mock_check.assert_called_once_with(
            ['changed_file.py'],
            base_branch_name_provided=None,
            diff=True,
            local_toml_path_provided=None,
            base_toml_path_provided=None,
        )


def test_main_invalid_mode() -> None:
    with patch('sys.argv', ['pystolint', 'invalid', 'some_file.py']), pytest.raises(SystemExit) as exc_info:
        main()
    assert exc_info.value.code != 0


def test_main_no_paths() -> None:
    with (
        patch('sys.argv', ['pystolint', 'check']),
        patch('sys.stderr', new=StringIO()) as stderr,
        pytest.raises(SystemExit) as exc_info,
    ):
        main()
        assert stderr.getvalue() == 'No paths provided'
        assert exc_info.value.code == 2


def test_process_paths_with_diff() -> None:
    with (
        patch('subprocess.run') as mock_run,
        patch('pathlib.Path.cwd') as mock_getcwd,
        patch('pystolint.main.get_git_changed_files') as mock_get_git_files,
    ):
        mock_run.return_value.stdout = '/path/to/git/root\n'
        mock_getcwd.return_value = '/path/to/git/root'
        mock_get_git_files.return_value = (['changed1.py'], ['changed2.py'])

        result = process_paths([], diff=True)
        assert result == ['changed1.py', 'changed2.py']


def test_process_paths_with_diff_not_in_git_root() -> None:
    with (
        patch('subprocess.run') as mock_run,
        patch('os.getcwd') as mock_getcwd,
        patch('sys.stderr', new=StringIO()) as stderr,
        pytest.raises(SystemExit) as exc_info,
    ):
        mock_run.return_value.stdout = '/path/to/git/root\n'
        mock_getcwd.return_value = '/different/path'

        process_paths([], diff=True)

        assert 'Error: Diff mode must be run from git repository root\n' in stderr.getvalue()
        assert exc_info.value.code == 1


def test_main_fails_with_paths_and_diff() -> None:
    with (
        patch('sys.argv', ['pystolint', 'check', 'some_file.py', '--diff']),
        patch('sys.stderr', new=StringIO()) as stderr,
        pytest.raises(SystemExit) as exc_info,
    ):
        main()
        assert stderr.getvalue() == 'Error: Diff mode does not accept file paths\n'
        assert exc_info.value.code == 1
