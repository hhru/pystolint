from __future__ import annotations

import re
import subprocess
from collections import defaultdict
from pathlib import Path
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from pystolint.util.toml import NestedDict

default_base_branch_name = 'master'


def get_git_changed_files(base_branch_name: str = default_base_branch_name) -> tuple[list[str], list[str]]:
    # Get tracked changes (modified or added files compared to base_branch_name)
    changed_files_proc = subprocess.run(
        ['git', 'diff', '--name-only', '-z', base_branch_name], capture_output=True, text=True, check=False
    )
    changed_files = changed_files_proc.stdout.split('\0')[:-1]
    changed_files = [str(Path.cwd() / path) for path in changed_files]

    # Handle untracked .py files
    untracked_output = subprocess.run(
        ['git', 'ls-files', '--others', '--exclude-standard', '-z'], capture_output=True, text=True, check=False
    )
    untracked_files = untracked_output.stdout.split('\0')[:-1]
    untracked_files = [str(Path.cwd() / path) for path in untracked_files]

    return changed_files, untracked_files


def get_git_changed_lines(base_branch_name: str = default_base_branch_name) -> dict[str, set[int]]:
    result = defaultdict(set)
    changed_files, untracked_files = get_git_changed_files(base_branch_name)

    for file_path in changed_files:
        if not file_path.endswith('.py'):
            continue
        diff_proc = subprocess.run(
            ['git', 'diff', '--unified=0', base_branch_name, '--', file_path],
            capture_output=True,
            text=True,
            check=False,
        )
        file_diff = diff_proc.stdout
        for line in file_diff.split('\n'):
            if line.startswith('@@'):
                match = re.search(r'\+(\d+)(?:,(\d+))?', line)
                if match:
                    start = int(match.group(1))
                    count = int(match.group(2)) if match.group(2) else 1
                    line_numbers = set(range(start, start + count))
                    result[file_path].update(line_numbers)

    for file_path in untracked_files:
        if file_path.endswith('.py'):
            try:
                lines = Path(file_path).read_text().splitlines()
                line_count = len(lines)
                if line_count > 0:
                    line_numbers = set(range(1, line_count + 1))
                    result[file_path].update(line_numbers)
            except FileNotFoundError:
                pass
            except OSError:
                pass

    return {k: v for k, v in result.items() if v}


def get_base_branch_name(base_branch_name_provided: str | None, merged_config: NestedDict) -> str:
    pystolint_settings = merged_config.get('pystolint', {})
    assert isinstance(pystolint_settings, dict)
    config_default = pystolint_settings.get('base_branch_name')
    assert config_default is None or isinstance(config_default, str)

    return base_branch_name_provided or config_default or default_base_branch_name
