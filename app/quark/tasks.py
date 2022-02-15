from common.decorators import close_db_connection
from . import contract
from celery import shared_task
from app.celery import app
import logging
from . import config
from .indexer import run_indexer

logger = logging.getLogger(__name__)

@app.task()
def add(x, y):
    return x + y

@app.task()
def xsum(x):
    return sum(x)

@app.task(bind=True)
@close_db_connection()
def update_all_events(self, environment):
    run_indexer(environment)


@shared_task
@close_db_connection()
def periodic_5_update_all_events():  # 5 mins
    for environment in config.Environment:
        update_all_events(environment)
