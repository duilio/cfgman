from collections.abc import Iterator

import pytest

import cfgman


@pytest.fixture(scope="module", autouse=True)
def cleanup() -> Iterator[None]:
    yield
    cfgman.reset()
