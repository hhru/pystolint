from __future__ import annotations

from enum import Enum
from pathlib import Path
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from collections.abc import Collection


# Remove when python3.9 support is dropped
class StrEnum(str, Enum):
    def __new__(cls, value: str) -> str:  # type: ignore[misc]
        obj = str.__new__(cls, value)
        obj._value_ = value
        return obj

    def __str__(self) -> str:
        return self.value  # type: ignore[no-any-return]


class Severity(StrEnum):
    Note = 'note'
    Error = 'error'


class ReportItem:
    def __init__(
        self, file_path: str, line: int, column: int, message: str, code: str = '', severity: Severity = Severity.Error
    ) -> None:
        self.file_path = file_path
        self.line = line
        self.column = column
        self.message = message
        self.severity = severity
        self.code = code

    def __str__(self) -> str:
        code = f'[{self.code}]' if self.code else ''
        file_path = Path(self.file_path)
        if file_path.is_absolute():
            file_path = file_path.relative_to(Path.cwd())

        return f'{file_path}:{self.line}:{self.column} – {self.severity}: {self.message} {code}'


class Report:
    def __init__(self, items: list[ReportItem] | None = None, errors: Collection[str] | None = None) -> None:
        self.items: list[ReportItem] = items or []
        self.errors: set[str] = set(errors or ())

    def __add__(self, other: Report) -> Report:
        return Report(items=self.items + other.items, errors=self.errors | other.errors)
