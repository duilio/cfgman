from dataclasses import asdict

from apischema import serialize

from configman import MISSING, configclass, get_default_config, load_config


@configclass
class WebServerConfig:
    host: str
    port: int


@configclass
class Config:
    web: WebServerConfig
    name: str
    values: list[int] | None = None


@configclass
class ConfigWithDefaults:
    name: str = "default"
    number: int = 10


def test_nested_config() -> None:
    config = load_config(
        Config,
        {"name": "foo"},
        {"web": {"host": "foo"}},
        {"web": {"host": "bar", "port": 80}},
        {"values": [1, 2]},
        {"values": [3]},
    )

    assert serialize(Config, config) == {
        "name": "foo",
        "values": [1, 2, 3],
        "web": {
            "host": "bar",
            "port": 80,
        },
    }


def test_callables() -> None:
    config = load_config(
        Config,
        lambda x: {"name": "foo", "values": [1]},
        lambda x: {"web": {"host": "localhost", "port": 80}},
    )

    assert serialize(Config, config) == {
        "name": "foo",
        "values": [1],
        "web": {"host": "localhost", "port": 80},
    }


default_config = {
    "web": {
        "host": "localhost",
        "port": 80,
    },
    "name": "my-server",
}


def load_default_config() -> None:
    load_config(Config, default_config)


def test_get_default() -> None:
    load_default_config()
    webconfig = get_default_config(WebServerConfig)
    assert webconfig.host == "localhost"
    assert webconfig.port == 80

    config = get_default_config(Config)
    assert config.values is None


def test_missing() -> None:
    config = load_config(
        Config,
        {"name": "foo", "values": [1], "web": {"host": "localhost", "port": 80}},
        {"name": MISSING, "web": MISSING},
    )

    assert asdict(config) == {
        "name": "foo",
        "values": [1],
        "web": {"host": "localhost", "port": 80},
    }


def test_missing_with_defaults() -> None:
    config_with_defaults = load_config(
        ConfigWithDefaults, {"name": MISSING, "number": 20}
    )

    assert asdict(config_with_defaults) == {
        "name": "default",
        "number": 20,
    }
