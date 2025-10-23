from __future__ import annotations

import tempfile
from typing import TYPE_CHECKING, cast

import tomli_w

from pystolint.dto.report import Report
from pystolint.mypy.mypy_check import run_mypy_check
from pystolint.ruff.ruff_check import run_ruff_check, run_ruff_format_check
from pystolint.ruff.ruff_format import run_ruff_check_fix, run_ruff_format
from pystolint.tools import Mode, Tool, get_available_tools
from pystolint.util.git import get_base_branch_name
from pystolint.util.paths import filter_excluded, filter_py_files
from pystolint.util.toml import get_merged_config

if TYPE_CHECKING:
    from collections.abc import Collection


def reformat(
    paths: list[str],
    *,
    local_toml_path_provided: str | None = None,
    base_toml_path_provided: str | None = None,
    tools: Collection[Tool] | None = None,
) -> str:
    tools = tools or get_available_tools(Mode.FORMAT)
    merged_config = get_merged_config(local_toml_path_provided, base_toml_path_provided).get('tool', {})
    assert isinstance(merged_config, dict)

    out = ''
    if Tool.RUFF in tools:
        with tempfile.NamedTemporaryFile(mode='w', suffix='.toml') as tmp_config:
            ruff_config = merged_config.get('ruff', {})
            assert isinstance(ruff_config, dict)
            toml_str = tomli_w.dumps(ruff_config)
            tmp_config.write(toml_str)
            tmp_config.flush()
            tmp_config_path = tmp_config.name

            out += run_ruff_format(tmp_config_path, paths)
            out += run_ruff_check_fix(tmp_config_path, paths)
    return out


def check(
    paths: list[str],
    *,
    base_branch_name_provided: str | None = None,
    diff: bool = False,
    local_toml_path_provided: str | None = None,
    base_toml_path_provided: str | None = None,
    tools: Collection[Tool] | None = None,
) -> Report:
    tools = tools or get_available_tools(Mode.CHECK)
    merged_config = get_merged_config(local_toml_path_provided, base_toml_path_provided).get('tool', {})
    assert isinstance(merged_config, dict)
    base_branch_name = get_base_branch_name(base_branch_name_provided, merged_config)

    report = Report()
    filtered_paths = filter_py_files(paths)
    if not filtered_paths:
        return report

    if Tool.RUFF in tools:
        ruff_config = merged_config.get('ruff', {})
        assert isinstance(ruff_config, dict)
        ruff_excluded = cast('list[str]', ruff_config.get('exclude', []))
        assert isinstance(ruff_excluded, list)
        ruff_paths = filter_excluded(filtered_paths, ruff_excluded) if diff else filtered_paths
        if len(ruff_paths) > 0:
            with tempfile.NamedTemporaryFile(mode='w', suffix='.toml') as tmp_config:
                toml_str = tomli_w.dumps(ruff_config)
                tmp_config.write(toml_str)
                tmp_config.flush()
                tmp_config_path = tmp_config.name

                report += run_ruff_check(tmp_config_path, ruff_paths, base_branch_name=base_branch_name, diff=diff)
                report += run_ruff_format_check(tmp_config_path, ruff_paths)

    if Tool.MYPY in tools:
        mypy_config = merged_config.get('mypy', {})
        assert isinstance(mypy_config, dict)
        mypy_excluded = cast('list[str]', mypy_config.get('exclude', []))
        assert isinstance(mypy_excluded, list)
        mypy_paths = filter_excluded(filtered_paths, mypy_excluded) if diff else filtered_paths

        if len(mypy_paths) > 0:
            with tempfile.NamedTemporaryFile(mode='w', suffix='.toml') as tmp_config:
                toml_str = tomli_w.dumps({'tool': {'mypy': mypy_config}})
                tmp_config.write(toml_str)
                tmp_config.flush()
                tmp_config_path = tmp_config.name

                report += run_mypy_check(tmp_config_path, mypy_paths, base_branch_name=base_branch_name, diff=diff)

    return report
