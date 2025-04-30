from __future__ import annotations

import re
from pathlib import Path
from typing import Union, cast

try:
    import tomllib  # type: ignore[import-not-found,unused-ignore]
except ImportError:
    import tomli as tomli_fallback  # type: ignore[import-not-found,unused-ignore]

    tomllib = tomli_fallback  # type: ignore[no-redef,unused-ignore]

NestedValue = Union['NestedDict', 'NestedList', str, int, float, bool, None]

NestedDict = dict[str, NestedValue]
NestedList = list[NestedValue]
py_versions_pattern = re.compile(r'^(>=|~=|>|\^|\s*)([\d.]+)')


def deep_merge(base_toml_dict: NestedDict, override_toml_dict: NestedDict) -> None:
    for key, value in override_toml_dict.items():
        if key in base_toml_dict and isinstance(base_toml_dict[key], dict) and isinstance(value, dict):
            deep_merge(cast('NestedDict', base_toml_dict[key]), cast('NestedDict', value))
        elif key in base_toml_dict and isinstance(base_toml_dict[key], list) and isinstance(value, list):
            cast('NestedList', base_toml_dict[key]).extend(cast('NestedList', value))
        else:
            base_toml_dict[key] = value


def get_base_toml_path(base_toml_path_provided: str | None, local_config: NestedDict) -> str:
    tool_settings = local_config.get('tool', {})
    assert isinstance(tool_settings, dict)
    pystolint_settings = tool_settings.get('pystolint', {})
    assert isinstance(pystolint_settings, dict)
    config_default = pystolint_settings.get('base_toml_path')
    assert config_default is None or isinstance(config_default, str)

    return (
        base_toml_path_provided or config_default or str(Path(__file__).parent.parent / 'default_config/pyproject.toml')
    )


def get_merged_config(
    local_toml_path_provided: str | None = None, base_toml_path_provided: str | None = None
) -> NestedDict:
    local_toml_path = local_toml_path_provided or 'pyproject.toml'
    local_config = tomllib.loads(Path(local_toml_path).read_text())

    base_toml_path = get_base_toml_path(base_toml_path_provided, local_config)
    default_config = tomllib.loads(Path(base_toml_path).read_text())

    python_target_version: str | None = get_python_min_version(local_config)
    if python_target_version is not None:
        default_config['tool']['ruff']['target-version'] = 'py' + python_target_version.replace('.', '')
        default_config['tool']['mypy']['python_version'] = python_target_version

    merged_config: NestedDict = default_config.copy()
    deep_merge(merged_config, local_config)

    return merged_config


def parse_min_version(version_spec: str) -> str | None:
    """
    Extract the minimal Python version from a version specifier.

    Returns:
        Optional[str] version in MAJOR.MINOR format

    """
    # Remove spaces and split on commas to handle multiple constraints
    constraints = version_spec.replace(' ', '').split(',')

    min_versions = []
    for constraint in constraints:
        # Match version numbers with different operators
        match = re.match(py_versions_pattern, constraint)
        if match:
            operator, version = match.groups()
            if operator in {'>=', '~=', '^', ''}:
                min_versions.append(version)
            elif operator == '>':
                # For '>3.8', the minimal is 3.9
                parts = version.split('.')
                if len(parts) == 1:
                    # Handle cases like '>3'
                    min_versions.append(parts[0] + '.0')
                else:
                    # Handle cases like '>3.8'
                    min_versions.append(f'{parts[0]}.{int(parts[1]) + 1}')

    if not min_versions:
        return None

    # Return the most restrictive minimal version
    return max(min_versions, key=lambda v: tuple(map(int, filter(None, v.split('.')))))


def get_python_min_version(local_config: NestedDict) -> str | None:
    version_spec = None

    # Check Poetry project
    if 'tool' in local_config and isinstance(local_config['tool'], dict) and 'poetry' in local_config['tool']:
        assert isinstance(local_config['tool']['poetry'], dict)
        dependencies = local_config['tool']['poetry'].get('dependencies', {})
        assert isinstance(dependencies, dict)
        version_spec = dependencies.get('python')

    # Check setuptools project (PEP 621)
    elif (
        'project' in local_config
        and isinstance(local_config['project'], dict)
        and 'requires-python' in local_config['project']
    ):
        version_spec = local_config['project']['requires-python']

    if not version_spec:
        return None

    assert isinstance(version_spec, str)
    result = parse_min_version(version_spec)
    if result is None:
        return None

    result = result.rstrip('.')
    assert re.match(r'^\d+\.\d+$', result), f'Version {result} does not match format MAJOR.MINOR'
    return result
