import time
from fastapi import APIRouter
from common.decorators import api_wrapper
from . import contract
from . import config
from typing import List
import logging

logger = logging.getLogger(__name__)

api_router = APIRouter()

@api_router.post("/update_events/{contract_address}/")
@api_wrapper
def update(contract_address: str, event_names: List[str], environment: config.Environment):
    contract.get(contract_address=contract_address,
                 environment=environment).update(event_names)
    time.sleep(3)
    return {}
