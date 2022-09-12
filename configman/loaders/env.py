import os
from collections.abc import Mapping, Sequence
from typing import Any, TypeVar

_T = TypeVar("_T")


def load_env(
    mapping: Mapping[str, str],
    cls: type[_T] = None,
    validate=False,
    subpath: str | Sequence[str] | None = None,
    prefix: str = "",
    env: Mapping[str, str] | None = None,
) -> dict[str, Any]:
    if env is None:
        env = os.environ.copy()

    return {}


def env_loader():
    ...
