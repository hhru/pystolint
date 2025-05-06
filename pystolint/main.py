from __future__ import annotations

import argparse
import subprocess
import sys
from pathlib import Path
from typing import TYPE_CHECKING

from pystolint.api import check, reformat
from pystolint.util.git import default_base_branch_name, get_git_changed_files

if TYPE_CHECKING:
    from pystolint.dto.report import Report


def format_with_stdout(
    paths: list[str], *, local_toml_path_provided: str | None = None, base_toml_path_provided: str | None = None
) -> None:
    out = reformat(
        paths, local_toml_path_provided=local_toml_path_provided, base_toml_path_provided=base_toml_path_provided
    )
    sys.stdout.write(out)


def check_with_stdout(
    paths: list[str],
    *,
    base_branch_name_provided: str | None = None,
    diff: bool = False,
    local_toml_path_provided: str | None = None,
    base_toml_path_provided: str | None = None,
) -> None:
    report: Report = check(
        paths,
        base_branch_name_provided=base_branch_name_provided,
        diff=diff,
        local_toml_path_provided=local_toml_path_provided,
        base_toml_path_provided=base_toml_path_provided,
    )

    for item in report.items:
        sys.stdout.write(str(item) + '\n')

    if len(report.items) > 0:
        sys.stdout.write(f'Found {len(report.items)} errors\n')
        for error in report.errors:
            sys.stderr.write(error + '\n')
        sys.exit(1)


def process_paths(paths: list[str], *, base_branch_name_provided: str | None = None, diff: bool = False) -> list[str]:
    if diff:
        if len(paths) != 0:
            sys.stderr.write('Error: Diff mode does not accept file paths\n')
            sys.exit(2)

        git_root = subprocess.run(
            ['git', 'rev-parse', '--show-toplevel'], capture_output=True, text=True, check=False
        ).stdout
        if not git_root or str(Path.cwd()) != git_root.strip():
            sys.stderr.write('Error: Diff mode must be run from git repository root\n')
            sys.exit(2)

        changed_files, untracked_files = get_git_changed_files(base_branch_name_provided or default_base_branch_name)
        paths = changed_files + untracked_files
    else:
        paths = [path if Path(path).is_absolute() else str(Path.cwd() / path) for path in paths]

    return paths


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument('mode', choices=['check', 'format'], help='must be either check or format', type=str)
    parser.add_argument('paths', nargs='*', help='paths to execute checks on', type=str)
    parser.add_argument('--diff', action='store_true', help='check only "git modified" files')
    parser.add_argument('--config', help='path to a TOML configuration file', default=None)
    parser.add_argument('--base_branch_name', help='base branch name for --diff mode (default master)', default=None)
    parser.add_argument(
        '--base_toml_path',
        help='path to a base TOML configuration file, if you want replace pystolint defaults',
        default=None,
    )
    args = parser.parse_args()
    base_branch_name_provided = args.base_branch_name
    base_toml_path_provided = args.base_toml_path
    local_toml_path_provided = args.config

    paths = process_paths(args.paths, base_branch_name_provided=base_branch_name_provided, diff=args.diff)
    if len(paths) == 0:
        sys.stderr.write('No paths provided')
        sys.exit(2)

    if args.mode == 'check':
        check_with_stdout(
            paths,
            base_branch_name_provided=base_branch_name_provided,
            diff=args.diff,
            local_toml_path_provided=local_toml_path_provided,
            base_toml_path_provided=base_toml_path_provided,
        )
    elif args.mode == 'format':
        format_with_stdout(
            paths, local_toml_path_provided=local_toml_path_provided, base_toml_path_provided=base_toml_path_provided
        )


if __name__ == '__main__':
    main()
