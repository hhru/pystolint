import os
from pathlib import Path

from _pytest.config.argparsing import Parser

ROOT = Path(__file__).parent.parent
os.chdir(ROOT)


def pytest_addoption(parser: Parser) -> None:
    parser.addoption('--github-actions', action='store_true', default=False)
