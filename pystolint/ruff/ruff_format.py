import sys

from pystolint.util import execute_command


def run_ruff_format(tmp_config_path: str, paths: list[str]) -> str:
    files_to_check = ' '.join(paths)
    ruff_cmd = ['ruff', 'format', '--config', tmp_config_path, *files_to_check.split()]
    _code, out, err = execute_command(ruff_cmd)
    sys.stderr.write(err)
    return out


def run_ruff_check_fix(tmp_config_path: str, paths: list[str]) -> str:
    files_to_check = ' '.join(paths)
    ruff_cmd = ['ruff', 'check', '--fix', '--config', tmp_config_path, *files_to_check.split()]
    _code, out, err = execute_command(ruff_cmd)
    sys.stderr.write(err)
    for line in out.splitlines():
        if line.strip().startswith('Found '):
            return line + '\n'

    return ''
