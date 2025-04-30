from pystolint.util.toml import NestedDict, deep_merge, parse_min_version


def test_deep_merge_dictionaries() -> None:
    base: NestedDict = {'tool': {'ruff': {'line-length': 100, 'select': ['E501']}}}
    override: NestedDict = {'tool': {'ruff': {'line-length': 120, 'ignore': ['E203']}}}

    deep_merge(base, override)
    assert isinstance(base['tool'], dict)
    assert isinstance(base['tool']['ruff'], dict)
    assert base['tool']['ruff']['line-length'] == 120
    assert base['tool']['ruff']['select'] == ['E501']
    assert base['tool']['ruff']['ignore'] == ['E203']


def test_deep_merge_lists() -> None:
    base: NestedDict = {'tool': {'ruff': {'select': ['E501']}}}
    override: NestedDict = {'tool': {'ruff': {'select': ['F401']}}}

    deep_merge(base, override)
    assert isinstance(base['tool'], dict)
    assert isinstance(base['tool']['ruff'], dict)
    assert base['tool']['ruff']['select'] == ['E501', 'F401']


def test_parse_min_version() -> None:
    # Test various version specifiers
    assert parse_min_version('>=3.8') == '3.8'
    assert parse_min_version('>=3.8,<4.0') == '3.8'
    assert parse_min_version('>3.8') == '3.9'
    assert parse_min_version('^3.8') == '3.8'
    assert parse_min_version('~=3.8') == '3.8'
    assert parse_min_version('>=3.8,>=3.9') == '3.9'


def test_parse_min_version_invalid() -> None:
    assert parse_min_version('invalid') is None
    assert parse_min_version('') is None
