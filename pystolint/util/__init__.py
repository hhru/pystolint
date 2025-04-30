import os
import subprocess
import sys
from pathlib import Path


def execute_command(cmd: list[str]) -> tuple[int, str, str]:
    completed_proc = subprocess.run(cmd, capture_output=True, shell=False, check=False, text=True)
    code = completed_proc.returncode
    out = completed_proc.stdout
    err = completed_proc.stderr

    if code > 1:
        sys.stderr.write(f'cmd {cmd} failed with: \n')
        sys.stderr.write(out)
        sys.stderr.write(err)
        sys.exit(code)

    return code, out, err


def filter_py_files(paths: list[str]) -> list[str]:
    # Filter out directories without .py files because mypy crashes on empty dirs
    py_files = []
    for path in paths:
        if Path(path).is_file() and path.endswith('.py'):
            py_files.append(path)
        elif Path(path).is_dir():
            has_py = False
            for _, __, files in os.walk(path):
                if any(f.endswith('.py') for f in files):
                    has_py = True
                    break
            if has_py:
                py_files.append(path)

    return py_files
