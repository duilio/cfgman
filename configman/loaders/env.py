import os
from collections.abc import Callable, Mapping, Sequence
from functools import partial
from typing import Any, TypeVar

from apischema import deserialize

from configman.tree import ensure_path_prefix, envelop_subpath

_T = TypeVar("_T")


def load_env(
    cls: type[_T] | None = None,
    *,
    mapping: Mapping[str, str],
    subpath: str | Sequence[str] | None = None,
    validate=False,
    prefix: str = "",
    env: Mapping[str, str] | None = None,
) -> dict[str, Any]:
    if env is None:
        env = os.environ

    if validate and cls is None:
        raise ValueError("Validation require `cls` being set.")

    # normalize keys to be case-insensitive and add prefix in the mapping keys
    env = {k.upper(): v for k, v in env.items()}
    mapping = {prefix + k.upper(): v for k, v in mapping.items()}

    result: dict[str, Any] = {}

    # iterate all mapping keys and populate the result tree
    for varname, nodepath in mapping.items():
        if varname not in env:
            continue

        node, key = ensure_path_prefix(result, nodepath.split("."))
        node[key] = env[varname]

    if validate:
        deserialize(cls, result, coerce=True)

    # envelop the result in a subpath if required.
    if subpath is None:
        return result

    if isinstance(subpath, str):
        subpath = subpath.split(".")

    return envelop_subpath(result, subpath)


def env_loader(
    *,
    cls: type[_T] = None,
    subpath: str | Sequence[str] | None = None,
    mapping: Mapping[str, str],
    validate=False,
    prefix: str = "",
    env: Mapping[str, str] | None = None,
) -> Callable[[type], dict[str, Any]]:
    """Return a function to load the environment."""

    wrapped_func = partial(
        load_env,
        mapping=mapping,
        validate=validate,
        subpath=subpath,
        prefix=prefix,
        env=env,
    )

    if cls is None:
        return wrapped_func
    else:
        return lambda x: wrapped_func(cls)
