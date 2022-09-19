from pathlib import Path

import apischema

from cfgman.types import FileType


class ConfigError(Exception):
    """cfgman configuration error."""


class NoConfigFileError(Exception):
    def __init__(self, paths: list[Path]):
        self._paths = paths

    def __str__(self) -> str:
        return (
            f"No config files in the following paths:"
            f" {', '.join(map(str, self._paths))}"
        )


class ValidationError(Exception):
    def __init__(self, filename: str, errors: apischema.ValidationError):
        self._filename = filename
        self._errors = errors

    def __str__(self) -> str:
        filename = self._filename
        errors = self._errors
        return f"Errors found in {filename}: {errors}"


class UnsupportedFileType(Exception):
    """The imported file is not supported."""

    def __init__(
        self, *, file_type: FileType | None = None, filename: str | None = None
    ):
        if file_type is None and filename is not None:
            msg = f"Cannot detect type for file '{filename}'"
        elif filename is None and file_type is not None:
            msg = f"{file_type.name} is not supported."
        elif file_type is not None:
            msg = f"{file_type.name} is not supported for file '{filename}'."
        else:
            msg = "Unsupported file type."
        super().__init__(msg)

        self.file_format = file_type
        self.filename = filename
