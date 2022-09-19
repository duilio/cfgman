import json
from dataclasses import asdict
from pathlib import Path
from textwrap import dedent

import pytest

from cfgman import configclass, load_config
from cfgman.errors import NoConfigFileError
from cfgman.loaders import file_loader, load_file


@configclass
class B:
    x: int


@configclass
class A:
    name: str
    number: int
    cls: B


def test_without_files() -> None:
    assert load_file(A, files=[]) == []


def test_without_existing_files(tmp_path: Path) -> None:
    files = [
        tmp_path / "missing_file.yaml",
        tmp_path / "missing_file.json",
    ]
    assert load_file(A, files=files) == []


def test_without_existing_files_but_one_required(tmp_path: Path) -> None:
    files = [
        tmp_path / "missing_file.yaml",
        tmp_path / "missing_file.json",
    ]

    with pytest.raises(NoConfigFileError):
        load_file(A, files=files, load_at_least_one_file=True)


def test_load(tmp_path: Path) -> None:
    obj = {"name": "hello", "number": "2", "cls": {"x": 3}}

    filename = tmp_path / "config.json"
    with open(filename, "w") as fout:
        json.dump(obj, fout)

    assert load_file(A, files=filename) == [obj]


def test_load_multiple_files(tmp_path: Path) -> None:
    obj1 = {"name": "obj1", "number": 1, "cls": {"x": 3}}
    obj2 = {"name": "obj2", "number": 2, "cls": {"x": 4}}

    files = [tmp_path / "cfg1.json", tmp_path / "cfg2.json"]

    for obj, filename in zip([obj1, obj2], files):
        with open(filename, "w") as fout:
            json.dump(obj, fout)

    assert load_file(A, files=files) == [obj1, obj2]


def test_one_file_exist(tmp_path: Path) -> None:
    obj = {"name": "hello", "number": 1, "cls": {"x": 3}}

    filename = tmp_path / "cfg2.json"
    with open(filename, "w") as fout:
        json.dump(obj, fout)

    assert load_file(
        A, files=[tmp_path / "cfg1.json", filename, tmp_path / "cfg3.json"]
    ) == [obj]


def test_some_files_exist_but_all_required(tmp_path: Path) -> None:
    obj = {"name": "hello", "number": 1, "cls": {"x": 3}}

    filename = tmp_path / "cfg2.json"
    with open(filename, "w") as fout:
        json.dump(obj, fout)

    with pytest.raises(FileNotFoundError):
        load_file(
            A,
            files=[tmp_path / "cfg1.json", filename, tmp_path / "cfg3.json"],
            load_all_files=True,
        )


def test_subpath(tmp_path: Path) -> None:
    filename = tmp_path / "cfg.json"
    with open(filename, "w") as fout:
        json.dump({"x": 10}, fout)

    assert load_file(B, files=[filename], subpath="a") == [{"a": {"x": 10}}]


def test_yaml(tmp_path: Path) -> None:
    filename = tmp_path / "cfg.yaml"
    with open(filename, "w") as fout:
        print(
            dedent(
                """\
                name: hello
                number: 1
                cls:
                  x: 1
                """
            ),
            file=fout,
        )

    assert load_file(A, files=filename) == [
        {"name": "hello", "number": 1, "cls": {"x": 1}}
    ]


def test_toml(tmp_path: Path) -> None:
    filename = tmp_path / "cfg.toml"
    with open(filename, "w") as fout:
        print(
            dedent(
                """\
                name = "hello"
                number = 1
                [cls]
                x = 1
                """
            ),
            file=fout,
        )

    assert load_file(A, files=filename) == [
        {"name": "hello", "number": 1, "cls": {"x": 1}}
    ]


def test_file_loader(tmp_path: Path) -> None:
    filename = tmp_path / "cfg.json"
    with open(filename, "w") as fout:
        json.dump({"x": 5}, fout)

    config = load_config(
        A,
        {"name": "hello", "number": 1},
        file_loader(cls=B, files=filename, subpath="cls"),
    )
    assert asdict(config) == {"name": "hello", "number": 1, "cls": {"x": 5}}
