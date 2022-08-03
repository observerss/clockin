import functools
import pickle
import time
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


def cached(seconds: int):
    def outer(func, cached={}):
        @functools.wraps(func)
        def inner(*args, **kwargs):
            key = pickle.dumps((args, kwargs))
            if key not in cached or time.time() - cached[key][0] > seconds:
                cached[key] = (time.time(), func(*args, **kwargs))
            return cached[key][1]

        return inner

    return outer


class Database(TypedDict):
    url: str


class Executor(TypedDict):
    threads: int


class Config(TypedDict):
    database: Database
    executor: Executor


@cached(seconds=60)
def get_config() -> Config:
    loaded: Config = yaml.load(open(config_path), yaml.CSafeLoader)
    logger.debug(loaded)
    return loaded
