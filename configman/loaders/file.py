"""File loaders.

Support multiple file formats and multiple files.
(e.g. default config + user overrides)

"""
import json
from collections.abc import Callable, Iterable, Sequence
from functools import partial
from pathlib import Path
from typing import Any, TypeVar, cast

import apischema

from configman.errors import (
    ConfigError,
    NoConfigFileError,
    UnsupportedFileType,
    ValidationError,
)
from configman.tree import envelop_subpath
from configman.types import FileType

try:
    import yaml

    YAML_EXISTS = True
except KeyError:  # pragma: no cover
    YAML_EXISTS = False

try:
    import tomli

    TOML_EXISTS = True
except KeyError:  # pragma: no cover
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
    files: Iterable[str | Path] | str | Path,
    subpath: str | Sequence[str] | None = None,
    supported_file_types: Sequence[FileType] | None = None,
    validate: bool = True,
    load_all_files: bool = False,
    load_at_least_one_file: bool = False,
) -> list[dict[str, Any]]:
    """Load a config file or multiple config files.

    Args:
        cls: class used for validation.
        files: either a file path or a list of file paths.
        subpath: wrap the result in the subpath of a new `dict`. Validation is
            done before wrapping.
        supported_file_types: list of supported file types. `None` means all of
            them.
        validate: validate the result.
        load_all_files: if `False` unexisting files are skipped.
        load_at_least_one_file: if `True` an exception is raised when no files
            are loaded.

    Returns:
        A list of dictionary to be used as a source for
        [`load_config`][configman.load_config].
    """
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

    return [envelop_subpath(x, subpath) for x in contents]


def file_loader(
    *,
    cls: type | None = None,
    subpath: str | Sequence[str] | None = None,
    files: Iterable[str | Path] | str | Path,
    supported_file_types: Sequence[FileType] | None = None,
    validate: bool = True,
    load_all_files: bool = False,
    load_at_least_one_file: bool = False,
) -> Callable[[type], list[dict[str, Any]]]:
    """Return a new loader to be used by [`load_config`][configman.load_config].

    This is just a wrapper for [`load_file`][configman.loaders.file.load_file].

    Args:
        cls: class used for validation.
        files: either a file path or a list of file paths.
        subpath: wrap the result in the subpath of a new `dict`. Validation is
            done before wrapping.
        supported_file_types: list of supported file types. `None` means all of
            them.
        validate: validate the result.
        load_all_files: if `False` unexisting files are skipped.
        load_at_least_one_file: if `True` an exception is raised when no files
            are loaded.

    Returns:
        A function that can be used as a source for the configuration.
            See [load_config][configman.load_config].
    """
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
                return cast(dict[str, Any], json.load(fin))
            case ".yaml" | ".yml":
                return cast(dict[str, Any], yaml.safe_load(fin))
            case ".toml":
                return tomli.load(fin)
            case _:
                assert False, "This should never happen."
