from collections.abc import Iterator

import pytest

import configman


@pytest.fixture(scope="module", autouse=True)
def cleanup() -> Iterator[None]:
    yield
    configman.reset()
