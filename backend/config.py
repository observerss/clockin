from typing import TypedDict
import yaml
import os
from logger import logger

ENV = os.environ.get("ENV", None)

if ENV == "production":
    filename = "prod.yaml"
else:
    filename = "dev.yaml"

config_path = os.path.join(os.path.dirname(__file__), "configs", filename)


class Database(TypedDict):
    url: str


class Executor(TypedDict):
    threads: int


class Config(TypedDict):
    database: Database
    executor: Executor


def get_config() -> Config:
    loaded: Config = yaml.load(open(config_path), yaml.CBaseLoader)
    logger.debug(loaded)
    return loaded
