import json
from pathlib import Path

from pystolint.dto.report import Report, ReportItem
from pystolint.util import execute_command
from pystolint.util.git import default_base_branch_name, get_git_changed_lines


def run_mypy_check(
    tmp_config_path: str,
    paths: list[str],
    *,
    base_branch_name: str = default_base_branch_name,
    diff: bool = False,
) -> Report:
    mypy_cmd = ['mypy', '--config-file', tmp_config_path, '--output', 'json', *paths]
    _code, out, err = execute_command(mypy_cmd)

    mypy_results = [json.loads(out_line) for out_line in out.splitlines() if out_line.strip()]

    modified_lines = get_git_changed_lines(base_branch_name) if diff else {}
    report = Report(errors=err.splitlines())
    for item in mypy_results:
        filename = item.get('file')
        if not Path(filename).is_absolute():
            filename = str(Path.cwd() / filename)

        line = int(item.get('line', '0'))
        if diff and (filename not in modified_lines or line not in modified_lines[filename]):
            continue
        column = int(item.get('column', '0'))
        message = item.get('message')
        report.items.append(ReportItem(filename, line, column, message))

    return report
