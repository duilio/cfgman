# configman

A configuration manager for Python application.

## Features

- Configure from files (yaml, toml, json).
- Environment variables.
- Custom variables (e.g. command line arguments).
- Type annotations.

## Usage

```python
from configman import configclass, load_config, get_default_config, env_loader, file_loader, MISSING
from apischema.metadata import conversion

def from_isoformat(s: str) -> datetime:
    return datetime.fromisoformat(s)

def to_isoformat(d: datetime) -> str:
    return d.isoformat()

@configclass
class WebServerConfig:
    host: str = 'localhost'
    port: int = 80
    timeout: int = 30

@configclass
class Config:
    web: WebServerConfig  # nest configs
    start: datetime = field(
        default_factory=lambda: datetime.now(datetime.utc),
        metadata=conversion(from_isoformat, to_isoformat)
    )

argparser = ArgumentParser(Config)
argparser.add_argument('-c', '--config', dest='config_files', metavar='FILENAME', action='append', default=['~/.config/myapp/config.yaml'])
argparser.add_argument('--host', metavar='HOSTNAME', default=MISSING)
argparser.add_argument('-p', '--port', metavar='PORT', type=int, default=MISSING)
argparser.add_argument('-s', '--start', metavar='ISODATETIME', default=MISSING)
args = argparser.parse_args()

config = load_config(
    Config,
    file_loader(files=args.config_files, supported_formats=(FileFormat.YAML, FileFormat.TOML)),
    env_loader(
        prefix='APP_',
        mapping={"HOST": "web.host", "PORT": "web.port"},
    ),
    {
        "web": {
            "host": args.host,
            "port": args.port,
        },
        "start": args.start,
    },
)

time.sleep((datetime.now(datetime.utc) - config.start).total_seconds)

async def run_server():
    # you can retrieve your module specific config without depending on the rest of the configuration
    webconfig = get_default_config(WebServerConfig)
    server = start_server(webconfig.host, webconfig.port)
    await server.serve_forever()

async def request_handler(request):
    experiment = select_experiment()
    with replace_default(WebServerConfig, changes=experiment.changes):
        webconfig = get_default_config(WebServerConfig)
        response = await prepare_response(headers={'X-Experiment-Name': webconfig.experiment})

```
