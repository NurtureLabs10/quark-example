from functools import wraps
import time
import logging

logger = logging.getLogger(__name__)

def _now():
    return time.time()

def timeit(f):
    def timed(*args, **kwargs):
        start_time = _now()
        response = f(*args, **kwargs)
        time_taken = _now() - start_time
        logger.debug(f'{f.__name__} took {time_taken} seconds')
        return response
    return timed