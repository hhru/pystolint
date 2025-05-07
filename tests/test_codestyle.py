import sys

from _pytest.config import Config
from conftest import ROOT

from pystolint.api import check


def test_codestyle(pytestconfig: Config) -> None:
    result = check(['.'], local_toml_path_provided=f'{ROOT}/pyproject.toml')
    if pytestconfig.getoption('--github-actions'):
        for item in result.items:
            file_name = item.file_path.removeprefix(str(ROOT) + '/')
            sys.stdout.write(f'::error file={file_name},line={item.line}::{item.message}\n')

    assert len(result.items) == 0, '\n'.join(str(item) for item in result.items)
    assert len(result.errors) == 0, '\n'.join(error for error in result.errors)
