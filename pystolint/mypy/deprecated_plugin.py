from __future__ import annotations

from typing import TYPE_CHECKING

from mypy import errorcodes
from mypy.plugin import FunctionContext, MethodContext, Plugin

if TYPE_CHECKING:
    from collections.abc import Callable

    from mypy.types import Type

DEPRECATED_DECORATOR_FQN = 'deprecated.Deprecated'


# will be deleted after up to 3.13+
# https://mypy.readthedocs.io/en/stable/changelog.html#support-for-deprecated-decorator-pep-702
class DeprecatedCheckerPlugin(Plugin):
    def get_function_hook(self, fullname: str) -> Callable[[FunctionContext], Type] | None:
        if DEPRECATED_DECORATOR_FQN in fullname:
            return self._handle_deprecated_call
        return None

    def get_method_hook(self, fullname: str) -> Callable[[MethodContext], Type] | None:
        if DEPRECATED_DECORATOR_FQN in fullname:
            return self._handle_deprecated_call
        return None

    @staticmethod
    def _handle_deprecated_call(ctx: MethodContext | FunctionContext) -> Type:
        ctx.api.fail('Call to deprecated function', ctx.context, code=errorcodes.DEPRECATED)
        return ctx.default_return_type


def plugin(version: str) -> type[DeprecatedCheckerPlugin]:  # noqa: ARG001
    return DeprecatedCheckerPlugin
