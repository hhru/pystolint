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
    assert parse_min_version('3.10.*') == '3.10'

    # Test wildcard patterns (the main issue that was fixed)
    assert parse_min_version('3.11.*') == '3.11'
    assert parse_min_version('3.9.*') == '3.9'
    assert parse_min_version('3.*') == '3.0'

    # Test exact versions
    assert parse_min_version('==3.8') == '3.8'
    assert parse_min_version('==3.8.0') == '3.8'
    assert parse_min_version('==3.8.1') == '3.8'

    # Test exclusive minimums with patch versions
    assert parse_min_version('>3.8.0') == '3.9'
    assert parse_min_version('>3.8.1') == '3.9'
    assert parse_min_version('>3.8') == '3.9'

    # Test complex constraints
    assert parse_min_version('>=3.8,<3.12') == '3.8'
    assert parse_min_version('>=3.9,<4.0') == '3.9'
    assert parse_min_version('>=3.8,>=3.9,<4.0') == '3.9'
    assert parse_min_version('>=3.8,') == '3.8'

    # Test caret ranges
    assert parse_min_version('^3.8.0') == '3.8'
    assert parse_min_version('^3.8.1') == '3.8'
    assert parse_min_version('^3.9.0') == '3.9'

    # Test tilde ranges
    assert parse_min_version('~=3.8.0') == '3.8'
    assert parse_min_version('~=3.8.1') == '3.8'
    assert parse_min_version('~=3.8.2') == '3.8'
