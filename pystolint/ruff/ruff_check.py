import json

from pystolint.dto.report import Report, ReportItem
from pystolint.util import execute_command
from pystolint.util.git import default_base_branch_name, get_git_changed_lines

IGNORE_DIFF_CODES = {'F841', 'F401', 'I001', 'I002'}


def run_ruff_format_check(tmp_config_path: str, paths: list[str]) -> Report:
    ruff_cmd = ['ruff', 'format', '--check', '--config', tmp_config_path, *paths]
    _code, out, err = execute_command(ruff_cmd)

    report = Report(errors=err.splitlines())
    if out:
        for line in out.splitlines():
            if line.startswith('Would reformat'):
                file_path = line.split('Would reformat: ', 1)[1]
                report.items.append(ReportItem(file_path, 0, 0, 'should be reformatted'))

    return report


def run_ruff_check(
    tmp_config_path: str,
    paths: list[str],
    *,
    base_branch_name: str = default_base_branch_name,
    diff: bool = False,
) -> Report:
    ruff_cmd = ['ruff', 'check', '--output-format', 'json', '--config', tmp_config_path, *paths]
    _code, out, err = execute_command(ruff_cmd)

    ruff_results = json.loads(out)
    modified_lines = get_git_changed_lines(base_branch_name) if diff else {}

    report = Report(errors=err.splitlines())
    for item in ruff_results:
        filename = item.get('filename')
        rule_code = item.get('code') or ''
        line = int(item.get('location', {}).get('row', '0'))
        if (
            diff
            and rule_code not in IGNORE_DIFF_CODES
            and (filename not in modified_lines or line not in modified_lines[filename])
        ):
            continue
        column = int(item.get('location', {}).get('column', '0'))
        message = rule_code + (': ' if rule_code else '') + item.get('message')
        report.items.append(ReportItem(filename, line, column, message))

    return report
