import os
from dataclasses import asdict

from pytest_mock import MockerFixture

from configman import configclass, load_config
from configman.loaders import env_loader, load_env


@configclass
class WebServerConfig:
    host: str = "localhost"
    port: int = 80


@configclass
class ApplicationConfig:
    web: WebServerConfig
    name: str


def test_load_env(mocker: MockerFixture) -> None:
    mocker.patch.dict(
        os.environ,
        {
            "FOO": "foo",
            "APP_HOST": "127.0.0.1",
            "APP_PORT": "8080",
            "APP_NAME": "myapp",
        },
    )

    configdict = load_env(
        ApplicationConfig,
        mapping={"HOST": "web.host", "PORT": "web.port", "NAME": "name"},
        validate=True,
        prefix="APP_",
    )
    assert configdict == {"name": "myapp", "web": {"host": "127.0.0.1", "port": "8080"}}


def test_env_loader(mocker: MockerFixture) -> None:
    mocker.patch.dict(
        os.environ,
        {
            "FOO": "foo",
            "APP_HOST": "127.0.0.1",
            "APP_PORT": "8080",
            "APP_NAME": "myapp",
        },
    )

    config = load_config(
        ApplicationConfig,
        env_loader(
            cls=ApplicationConfig,
            mapping={"HOST": "web.host", "PORT": "web.port", "NAME": "name"},
            validate=True,
            prefix="APP_",
        ),
    )

    assert asdict(config) == {
        "name": "myapp",
        "web": {"host": "127.0.0.1", "port": 8080},
    }
