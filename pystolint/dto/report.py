from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from collections.abc import Collection


class ReportItem:
    def __init__(self, file_path: str, line: int, column: int, message: str) -> None:
        self.file_path = file_path
        self.line = line
        self.column = column
        self.message = message

    def __str__(self) -> str:
        return f'{self.file_path}:{self.line}:{self.column}: {self.message}'


class Report:
    def __init__(self, items: list[ReportItem] | None = None, errors: Collection[str] | None = None) -> None:
        self.items: list[ReportItem] = items or []
        self.errors: set[str] = set(errors or ())

    def __add__(self, other: Report) -> Report:
        return Report(items=self.items + other.items, errors=self.errors | other.errors)
