"""Some internal functions to manipulate trees.

In this context, trees are nested trees where keys are strings and values are
either trees or Any.

"""
from collections.abc import Mapping, Sequence
from typing import Any, NamedTuple

NodePath = Sequence[str]
Node = dict[str, Any]


class ItemPtr(NamedTuple):
    node: Node
    key: str


def ensure_path_prefix(tree: Node, path: NodePath) -> ItemPtr:
    """Ensure the path prefix exists in the tree and return the item pointer.

    NOTE: this function change the tree in-place, adding the required path
    nodes.

    >>> ensure_path_prefix({}, ("a", "b", "c")) == ItemPtr({}, "c")
    True
    >>> tree = {"a": {}}
    >>> ensure_path_prefix(tree, ("a", "b", "c"))
    ItemPtr(node={}, key="c")
    >>> tree == {"a": {"b": {}}}
    True

    """
    if not path:
        raise ValueError("path must contain at least one element.")

    node = tree
    *partial_path, last_key = path
    for key in partial_path:
        node = node.setdefault(key, {})
    return ItemPtr(node, last_key)


def envelop_subpath(tree: Node, subpath: NodePath) -> Node:
    """Return a new tree containing the previous one in a subpath."""

    for k in reversed(subpath):
        tree = {k: tree}
    return tree


def copy(tree: Node) -> Node:
    """Copy a tree.

    This is not a shallow copy of the dict: it recursively copy all contained
    dicts. It also copies all lists in the tree.

    It is not a deep copy either: lists are not recursively copies and we are
    not going to copy any other object as they should be immutable or treated
    as those by the rest of the tree operations.

    """
    tree = tree.copy()
    for k, v in tree.items():
        if isinstance(v, Mapping):
            tree[k] = copy(tree[k])
        elif isinstance(v, list):
            tree[k] = v.copy()
    return tree
