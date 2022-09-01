import asyncio
import functools
from logger import logger

SUCCESS = dict(code=0, msg="ok")


def handles_error(func):
    @functools.wraps(func)
    def wrapper(*args, **kwargs):
        try:
            result = func(*args, **kwargs)
            if result is None:
                return SUCCESS
        except Exception as e:
            logger.exception(str(e))
            return dict(code=500, msg=str(e))

    return wrapper
