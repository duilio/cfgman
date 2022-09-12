import pytest

import configman


@pytest.fixture(scope="module", autouse=True)
def cleanup():
    yield
    configman.reset()
