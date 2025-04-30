import sys

from pystolint.api import check


def test_codestyle() -> None:
    result = check(['.'])
    for item in result.items:
        sys.stderr.write(str(item) + '\n')
    assert len(result.items) == 0
