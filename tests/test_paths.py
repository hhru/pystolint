from __future__ import annotations

from typing import TYPE_CHECKING, TypedDict

import pytest

from pystolint.util.paths import filter_excluded, filter_py_files

if TYPE_CHECKING:
    from pathlib import Path


class TmpStructureDict(TypedDict):
    root: Path
    dirs: dict[str, Path]
    files: dict[str, Path]


@pytest.fixture
def tmp_structure(tmp_path: Path) -> TmpStructureDict:
    (tmp_path / 'dir_with_py').mkdir()
    (tmp_path / 'dir_with_py' / 'file1.py').write_text('print("x")')
    (tmp_path / 'dir_empty').mkdir()
    (tmp_path / 'dir_no_py').mkdir()
    (tmp_path / 'dir_no_py' / 'data.txt').write_text('abc')
    (tmp_path / 'single.py').write_text('x=1')
    (tmp_path / 'not_python.txt').write_text('no')
    return {
        'root': tmp_path,
        'dirs': {
            'with_py': tmp_path / 'dir_with_py',
            'empty': tmp_path / 'dir_empty',
            'no_py': tmp_path / 'dir_no_py',
        },
        'files': {
            'py': tmp_path / 'single.py',
            'non_py': tmp_path / 'not_python.txt',
        },
    }


def test_filter_py_files_includes_py_files(tmp_structure: TmpStructureDict) -> None:
    paths = [
        str(tmp_structure['files']['py']),
        str(tmp_structure['files']['non_py']),
        str(tmp_structure['dirs']['with_py']),
        str(tmp_structure['dirs']['empty']),
        str(tmp_structure['dirs']['no_py']),
    ]

    result = filter_py_files(paths)

    assert str(tmp_structure['files']['py']) in result
    assert str(tmp_structure['dirs']['with_py']) in result
    assert str(tmp_structure['files']['non_py']) not in result
    assert str(tmp_structure['dirs']['empty']) not in result
    assert str(tmp_structure['dirs']['no_py']) not in result


def test_filter_py_files_ignores_nonexistent(tmp_path: Path) -> None:
    paths = [str(tmp_path / 'missing_dir'), str(tmp_path / 'missing_file.py')]
    assert filter_py_files(paths) == []


def test_filter_excluded_removes_matching_patterns() -> None:
    files = ['src/main.py', 'tests/test_main.py', 'build/script.py']
    excluded = ['^tests/', 'build']
    result = filter_excluded(files, excluded)
    assert 'src/main.py' in result
    assert 'tests/test_main.py' not in result
    assert 'build/script.py' not in result


def test_filter_excluded_handles_malformed_regex() -> None:
    files = ['a.py', 'b.py']
    excluded = ['[unclosed', 'b\\.py']
    result = filter_excluded(files, excluded)
    assert 'a.py' in result
    assert 'b.py' not in result


def test_filter_excluded_ignores_empty_patterns() -> None:
    files = ['a.py', 'b.py']
    excluded = [' ', '']
    result = filter_excluded(files, excluded)
    assert result == files


def test_filter_excluded_no_excludes() -> None:
    files = ['a.py', 'b.py']
    assert filter_excluded(files, []) == files
