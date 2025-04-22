import os
import subprocess
from collections.abc import Generator
from pathlib import Path

import pytest

from pystolint.util.git import get_git_changed_files, get_git_changed_lines


@pytest.fixture
def git_repo(tmp_path: Path) -> Generator[Path]:
    """
    Create a temporary git repository with initial commit.

    Yields:
        Path: path of git root dir

    """
    repo_dir = tmp_path / 'test_repo'
    repo_dir.mkdir()
    os.chdir(repo_dir)

    # Initialize git repo
    subprocess.run(['git', 'init'], check=True)
    subprocess.run(['git', 'config', 'user.email', 'test@example.com'], check=True)
    subprocess.run(['git', 'config', 'user.name', 'Test User'], check=True)

    # Create and commit initial file
    (repo_dir / 'initial.py').write_text("print('initial')\n")
    subprocess.run(['git', 'add', 'initial.py'], check=True)
    subprocess.run(['git', 'commit', '-m', 'Initial commit'], check=True)

    # Create master branch (to match the code's assumptions)
    subprocess.run(['git', 'branch', '-M', 'master'], check=True)

    yield repo_dir

    # Cleanup - return to original directory
    os.chdir(str(Path.cwd().parent))


def test_get_git_changed_files_modified(git_repo: Path) -> None:
    """Test detection of modified files."""
    # Modify existing file
    (git_repo / 'initial.py').write_text("print('modified')\n")

    # Create new tracked file
    (git_repo / 'new_tracked.py').write_text("print('new tracked')\n")
    subprocess.run(['git', 'add', 'new_tracked.py'], check=True)

    # Create untracked file
    (git_repo / 'untracked.py').write_text("print('untracked')\n")

    # Test with new_files_separated=True
    changed, untracked = get_git_changed_files()
    assert set(changed) == {str(git_repo / 'initial.py'), str(git_repo / 'new_tracked.py')}
    assert set(untracked) == {str(git_repo / 'untracked.py')}

    # Test with new_files_separated=False
    changed_files, untracked_files = get_git_changed_files()
    all_changes = changed_files + untracked_files
    assert set(all_changes) == {
        str(git_repo / 'initial.py'),
        str(git_repo / 'new_tracked.py'),
        str(git_repo / 'untracked.py'),
    }


def test_get_git_changed_lines(git_repo: Path) -> None:
    """Test detection of changed lines in files."""
    # Create a multi-line file and commit it
    initial_content = 'def foo():\n    return 42\n\ndef bar():\n    return 43\n'
    (git_repo / 'multi_line.py').write_text(initial_content)
    subprocess.run(['git', 'add', 'multi_line.py'], check=True)
    subprocess.run(['git', 'commit', '-m', 'Add multi-line file'], check=True)

    # Modify specific lines
    modified_content = 'def foo():\n    return 420\n\ndef bar():\n    return 43\n'
    (git_repo / 'multi_line.py').write_text(modified_content)

    # Create new file
    (git_repo / 'new_file.py').write_text("print('new')\n")

    changed_lines = get_git_changed_lines()

    # Check modified file
    multi_line_path = str(git_repo / 'multi_line.py')
    assert multi_line_path in changed_lines
    assert 2 in changed_lines[multi_line_path]  # Line with return 420

    # Check new file
    new_file_path = str(git_repo / 'new_file.py')
    assert new_file_path in changed_lines
    assert changed_lines[new_file_path] == {1}  # All lines in new file should be marked as changed


def test_get_git_changed_lines_with_deletions(git_repo: Path) -> None:
    """Test detection of changed lines when lines are deleted."""
    # Create initial file with multiple lines
    initial_content = 'line1\nline2\nline3\nline4\n'
    (git_repo / 'delete_test.py').write_text(initial_content)
    subprocess.run(['git', 'add', 'delete_test.py'], check=True)
    subprocess.run(['git', 'commit', '-m', 'Add file for deletion test'], check=True)

    # Delete some lines
    modified_content = 'line1\nline4\n'
    (git_repo / 'delete_test.py').write_text(modified_content)

    changed_lines = get_git_changed_lines()
    assert 'delete_test.py' not in changed_lines
