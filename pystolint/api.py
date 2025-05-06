from __future__ import annotations

import tempfile

import tomli_w

from pystolint.dto.report import Report
from pystolint.mypy.mypy_check import run_mypy_check
from pystolint.ruff.ruff_check import run_ruff_check, run_ruff_format_check
from pystolint.ruff.ruff_format import run_ruff_check_fix, run_ruff_format
from pystolint.util import filter_py_files
from pystolint.util.git import get_base_branch_name
from pystolint.util.toml import get_merged_config


def reformat(
    paths: list[str], *, local_toml_path_provided: str | None = None, base_toml_path_provided: str | None = None
) -> str:
    merged_config = get_merged_config(local_toml_path_provided, base_toml_path_provided).get('tool', {})
    assert isinstance(merged_config, dict)

    with tempfile.NamedTemporaryFile(mode='w', suffix='.toml') as tmp_config:
        ruff_config = merged_config.get('ruff', {})
        assert isinstance(ruff_config, dict)
        toml_str = tomli_w.dumps(ruff_config)
        tmp_config.write(toml_str)
        tmp_config.flush()
        tmp_config_path = tmp_config.name

        out = run_ruff_format(tmp_config_path, paths)
        out += run_ruff_check_fix(tmp_config_path, paths)

    return out


def check(
    paths: list[str],
    *,
    base_branch_name_provided: str | None = None,
    diff: bool = False,
    local_toml_path_provided: str | None = None,
    base_toml_path_provided: str | None = None,
) -> Report:
    merged_config = get_merged_config(local_toml_path_provided, base_toml_path_provided).get('tool', {})
    assert isinstance(merged_config, dict)
    base_branch_name = get_base_branch_name(base_branch_name_provided, merged_config)

    report = Report()
    filtered_paths = filter_py_files(paths)
    if not filtered_paths:
        return report

    with tempfile.NamedTemporaryFile(mode='w', suffix='.toml') as tmp_config:
        ruff_config = merged_config.get('ruff', {})
        assert isinstance(ruff_config, dict)
        toml_str = tomli_w.dumps(ruff_config)
        tmp_config.write(toml_str)
        tmp_config.flush()
        tmp_config_path = tmp_config.name

        report += run_ruff_check(tmp_config_path, filtered_paths, base_branch_name=base_branch_name, diff=diff)
        report += run_ruff_format_check(tmp_config_path, filtered_paths)

    with tempfile.NamedTemporaryFile(mode='w', suffix='.toml') as tmp_config:
        mypy_config = merged_config.get('mypy', {})
        mypy_config = {'tool': {'mypy': mypy_config}}
        assert isinstance(mypy_config, dict)
        toml_str = tomli_w.dumps(mypy_config)
        tmp_config.write(toml_str)
        tmp_config.flush()
        tmp_config_path = tmp_config.name

        report += run_mypy_check(tmp_config_path, filtered_paths, base_branch_name=base_branch_name, diff=diff)

    return report
