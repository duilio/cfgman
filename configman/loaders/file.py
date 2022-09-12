import json
from collections.abc import Callable, Iterable, Sequence
from functools import partial
from pathlib import Path
from typing import Any, TypeVar

import apischema

from configman.errors import (
    ConfigError,
    NoConfigFileError,
    UnsupportedFileType,
    ValidationError,
)
from configman.types import FileType

try:
    import yaml

    YAML_EXISTS = True
except KeyError:
    YAML_EXISTS = False

try:
    import tomli

    TOML_EXISTS = True
except KeyError:
    TOML_EXISTS = False


_T = TypeVar("_T")


file_suffixes = {
    ".json": FileType.JSON,
    ".yaml": FileType.YAML,
    ".yml": FileType.YAML,
    ".toml": FileType.TOML,
}


def load_file(
    cls: type[_T],
    *,
    subpath: str | Sequence[str] | None = None,
    files: Iterable[str | Path] | str | Path,
    supported_file_types: Sequence[FileType] | None = None,
    validate=True,
    load_all_files=False,
    load_at_least_one_file=False,
) -> list[dict[str, Any]]:
    """Load a config file or multiple config files."""

    # if supported_file_types is None, then it means all supported files.
    if supported_file_types is None:
        supported_file_types = [FileType.JSON]
        if YAML_EXISTS:
            supported_file_types.append(FileType.YAML)
        if TOML_EXISTS:
            supported_file_types.append(FileType.TOML)

    # check all required libraries are installed.
    if not YAML_EXISTS and FileType.YAML in supported_file_types:
        raise ConfigError("YAML support required but PyYAML is not installed.")
    if not TOML_EXISTS and FileType.TOML in supported_file_types:
        raise ConfigError("TOML support required but tomli is not installed.")

    # load all files
    if isinstance(files, Path | str):
        files = [Path(files)]

    all_paths = [Path(x) for x in files]

    if not load_all_files:
        paths = [x for x in all_paths if x.is_file()]
    else:
        paths = all_paths

    if load_at_least_one_file and not paths:
        raise NoConfigFileError(all_paths)

    contents = [_load_single_file(fname, supported_file_types) for fname in paths]

    # check against the schema
    if validate:
        for fname, content in zip(paths, contents):
            try:
                apischema.deserialize(cls, content, coerce=True)
            except apischema.ValidationError as errors:
                raise ValidationError(str(fname), errors)

    if subpath is None:
        return contents

    if isinstance(subpath, str):
        subpath = subpath.split(".")

    return [_apply_subpath(subpath, x) for x in contents]


def file_loader(
    *,
    cls: type | None = None,
    subpath: str | Sequence[str] | None = None,
    files: Iterable[str | Path] | str | Path,
    supported_file_types: Sequence[FileType] | None = None,
    validate=True,
    load_all_files=False,
    load_at_least_one_file=False,
) -> Callable[[type], list[dict[str, Any]]]:
    """Return a function to load the given files."""

    wrapped_func = partial(
        load_file,
        subpath=subpath,
        files=files,
        supported_file_types=supported_file_types,
        validate=validate,
        load_all_files=load_all_files,
        load_at_least_one_file=load_at_least_one_file,
    )

    if cls is None:
        return wrapped_func
    else:
        return lambda x: wrapped_func(cls)


def _apply_subpath(subpath: Sequence[str], content: dict[str, Any]) -> dict[str, Any]:
    for k in reversed(subpath):
        content = {k: content}
    return content


def _load_single_file(
    filename: Path, supported_file_types: Sequence[FileType]
) -> dict[str, Any]:
    with open(filename, "rb") as fin:
        try:
            file_type = file_suffixes[filename.suffix]
        except KeyError:
            raise UnsupportedFileType(filename=str(filename))

        if file_type not in supported_file_types:
            raise UnsupportedFileType(file_type=file_type, filename=str(filename))

        match filename.suffix:
            case ".json":
                return json.load(fin)
            case ".yaml" | ".yml":
                return yaml.safe_load(fin)
            case ".toml":
                return tomli.load(fin)
            case _:
                assert False, "This should never happen."
