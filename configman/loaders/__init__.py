"""
`Loaders` retrieve data from sources such as files and environment variables
and create a tree to be used by [`load_config`][configman.load_config].

A loader is just a function that takes parameter and return a dictionary.
A loader factory is a wrapper over a loader which accepts only one parameter:
a configclass used for the result validation.

`load_config` normally treats all callables as function loader of this kind
and pass them the configclass of the configuration we are loading.

# subpath

In some situations you might want to validate only a subset of a configuration,
in these cases the `subpath` argument of the loader may be handy.

```python
@configclass
class ServerConfig:
    host: str
    port: int

@configclass
class ApplicationConfig:
    name: str = "spam"
    server: ServerConfig

config = load_config(
    ApplicationConfig,
    file_loader(cls=ServerConfig, subpath="server", files=["~/.spam.json"])
)
```

The result loaded by file path will be first validated against the `cls` schema
and then wrapped in a tree at the given subpath.

!!! Note

    We are passing the `cls` parameter, otherwise the validation would be
    performed against the `ApplicationConfig` schema *before* the wrapping. Not what
    we want!

"""

from .env import env_loader as env_loader
from .env import load_env as load_env
from .file import file_loader as file_loader
from .file import load_file as load_file

__all__ = ["env_loader", "load_env", "file_loader", "load_file"]
