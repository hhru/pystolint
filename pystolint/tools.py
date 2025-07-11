from __future__ import annotations

from enum import Enum


class Mode(str, Enum):
    CHECK = 'check'
    FORMAT = 'format'


class Tool(str, Enum):
    MYPY = 'mypy'
    RUFF = 'ruff'


CHECK_TOOLS = {Tool.MYPY, Tool.RUFF}
FORMAT_TOOLS = {Tool.RUFF}

MODE_TOOLS = {
    Mode.CHECK: CHECK_TOOLS,
    Mode.FORMAT: FORMAT_TOOLS,
}


def get_available_tools(mode: Mode) -> set[Tool]:
    return MODE_TOOLS.get(mode, set())
