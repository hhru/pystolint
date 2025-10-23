import os
import re
from pathlib import Path


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


def filter_excluded(file_paths: list[str], excluded_patterns: list[str]) -> list[str]:
    # Filter out files excluded by ruff/mypy config
    compiled_patterns: list[re.Pattern[str]] = []
    for pattern in excluded_patterns:
        pattern_to_add = pattern.strip()
        if not pattern_to_add:
            continue
        try:
            compiled_patterns.append(re.compile(pattern_to_add))
        except re.error:
            # Ignore malformed excludes
            continue

    return [p for p in file_paths if not any(r.search(p) for r in compiled_patterns)]
