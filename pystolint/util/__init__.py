import subprocess
import sys


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
