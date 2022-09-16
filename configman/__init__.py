"""
configman is a configuration manager for python.

It provides some utility to:

- combine configuration from different sources (e.g. files, environment
  variables, ...)
- validate the configuration (via apischema)



"""
from collections.abc import Callable, Iterable, Iterator, Mapping, MutableMapping
from dataclasses import MISSING, dataclass, fields, is_dataclass
from typing import Any, TypeVar, cast

from apischema import deserialize
from typing_extensions import dataclass_transform

from .loaders import env_loader, file_loader  # noqa: F401
from .tree import Node, NodePath, copy, ensure_path_prefix

_T = TypeVar("_T")


register = set[type]()
defaults: dict[type, Any] = {}

__all__ = ["MISSING", "configclass", "load_config", "reset", "get_default_config"]


@dataclass_transform()
def configclass(cls: type[_T]) -> type[_T]:
    """Register the class as a config class.

    If the class is not already a [`dataclass`][dataclasses], apply the
    [`dataclass`][dataclasses.dataclass] decorator too.

    Args:
      cls: class to register.

    Returns:
      Either `cls` or `dataclass(cls)`.

    Examples:
        Define a new configclass.

        >>> @configclass
        ... class A:
        ...    x: int
    """
    if not is_dataclass(cls):
        datacls = dataclass(cls)
    else:
        datacls = cls

    register.add(datacls)
    return datacls


def load_config(
    cls: type[_T],
    *sources: dict[str, Any]
    | Callable[[type[_T]], dict[str, Any] | list[dict[str, Any]]],
) -> _T:
    """Load a configuration from multiple sources.

    The order of the sources matters: the first one is the lowest priority one
    (e.g. default values), the last one is the highest priority one (e.g. command
    line parameters).

    Default instances of the `configclasses` in the result tree will be assigned
    if the configuration is loaded correctly.

    Args:
        cls: configuration class to use for both validation and deserialization.
        *sources: configuration sources. A source can be a regular `dict` or a
            [loader][configman.loaders].

    Returns:
        An instance of the `configclass` with the data resulting from the merged
            sources.

    """
    if cls not in register:
        raise ValueError("First argument of load_config must be a configclass.")

    unflattened_layers = (x(cls) if callable(x) else x for x in sources)
    layers: list[dict[str, Any]] = []

    for x in unflattened_layers:
        if isinstance(x, Iterable) and not isinstance(x, Mapping):
            layers.extend(x)
        else:
            layers.append(x)

    config = deserialize(cls, _merge_layers(*layers), coerce=True)

    # set default configs
    # NOTE: if the same configclass appears multiple times, the last is the default one.
    for node in _visit_config(config):
        assert (
            is_dataclass(node) and not isinstance(node, type) and type(node) in register
        )
        defaults[type(node)] = node

    return config


def _visit_config(obj: Any) -> Iterator[Any]:
    """Visit the config tree and returns all registered configclasses."""

    if isinstance(obj, type):
        # excludes cases where you have a class/type as a value
        pass
    elif is_dataclass(obj):
        if type(obj) in register:
            yield obj
        for f in fields(obj):
            value = getattr(obj, f.name)
            yield from _visit_config(value)

    elif isinstance(obj, Mapping):
        for value in obj.values():
            yield from _visit_config(value)

    elif isinstance(obj, str | bytes):
        # exclude strings, otherwise they are considered iterables
        pass

    elif isinstance(obj, Iterable):
        for value in obj:
            yield from _visit_config(value)


def _merge_layers(*layers: dict[str, Any]) -> dict[str, Any]:
    """Merge multiple layers into a single one following magic rules.

    Rules:
    - an item is replaced if it is not a dict or a list.
    - dict are merged recusively.
    - lists are joined.
    - nodes containing a MISSING value are pruned.
    """
    head, *tail = layers
    current = copy(head)

    for layer in tail:
        for node_path, node_value in _visit_dict(layer):
            _merge_node_path(current, node_path, node_value)

    _prune_missing_inplace(current)
    return current


def _prune_missing_inplace(d: MutableMapping[str, Any]) -> None:
    """Prune all nodes containing a MISSING values."""

    to_del = []

    for k, v in d.items():
        if v is MISSING:
            to_del.append(k)
        elif isinstance(v, MutableMapping) and v:
            _prune_missing_inplace(v)

    for k in to_del:
        del d[k]


def _visit_dict(root: Node) -> Iterator[tuple[list[str], Any]]:
    """Visit the tree of a dict and yields all node paths.

    Each nested dictionary is visited recursively.
    """
    for key, value in root.items():
        if isinstance(value, dict):
            value = cast(Node, value)
            for node_path, node_value in _visit_dict(value):
                yield [key] + node_path, node_value
        else:
            yield [key], value


def _merge_node_path(tree: Node, path: NodePath, new_value: Any) -> None:
    """Merge the value of a node path with the new value.

    The values is overridden if it is not a list, otherwise the two lists are
    concatenated.
    """
    node, key = ensure_path_prefix(tree, path)

    # don't make any change if the new value is missing
    if new_value is MISSING:
        return

    if isinstance(new_value, list):
        current_value = node.get(key, MISSING)
        if current_value is MISSING:
            current_value = node[key] = []

        if not isinstance(current_value, list):
            raise TypeError(
                f"Setting {'.'.join(path)} has mixed type 'list' and non-'list'."
            )
        else:
            current_value.extend(new_value)
    else:
        node[key] = new_value


def get_default_config(cls: type[_T]) -> _T:
    """Return the default configuration for the given `configclass`.

    Default config instances are created once
    [`load_config`][configman.load_config] has been called successfully.

    Note:
        If a class has been instantiated multiple times (because `load_config`
        has been called multiple times or because it has multiple places in the
        configuration) the last instance is considered the default one.

    Args:
        cls: the requested type of the default instance.

    Raises:
        KeyError: if the class is not registered via
            [`configclass`][configman.configclass].

    Returns:
        The default instance for `cls`.
    """
    return cast(_T, defaults[cls])


def reset() -> None:
    """Reset the default configclasses.

    *Warning*: this is an utility function for tests, you hardly need to use
    this in your app.
    """
    defaults.clear()
