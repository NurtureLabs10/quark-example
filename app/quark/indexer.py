from .config import Environment
import importlib
import logging
from . import contract
from . import models
from pipe import select, where
from .services.event_scanner import update_events
from .services import web3_service
from web3 import Web3

logger = logging.getLogger(__name__)

# Add all the `index` apps you want to actively index  
INDEXERS_TO_SCAN = [
    "index_v1",
]

# Add a tag to quick access the index app
INDEX_MAPPING_BY_TAG = {
    "usdc_token": "index_v1",
}

def get_index_by_tag(tag):
    index = INDEX_MAPPING_BY_TAG[tag]
    return importlib.import_module(f"{index}")

def get_base_logs(tag):
    return get_index_by_tag(tag).models.TransactionLog


def get_checksum_address(address):
    return Web3.toChecksumAddress(address)


def get_contract_instance(index, contract_address, environment, abi_path, callbacks={}):
    contract_instance = web3_service.Contract(
        index=index,
        contract_address=get_checksum_address(contract_address),
        environment=environment,
        abi_path=abi_path,
    )

    if callbacks:
        contract_instance.add_callbacks(callbacks)
    return contract_instance


def run_indexer(environment):

    contract.register_all_contracts()

    # Get all the index apps
    for index in INDEXERS_TO_SCAN:
        _run(index, environment)


def _run(index, environment):
    logger.info(f"Runing indexer for environment: {environment}")

    try:
        all_contracts = importlib.import_module(f"{index}.contract_registry").get_registry()
        registry = list(
            all_contracts
            | where(
                lambda contract_details: contract_details["environment"] == environment
            )
        )

    except Exception as e:
        logger.exception(e)

    contracts_in_index = list(
        registry
        | select(
            lambda contract_details: get_contract_instance(
                index=index, **contract_details
            )
        )
    )
    if contracts_in_index:
        update_events(contracts_in_index, index)


def clear(index):
    index_models = None
    index_config = None
    try:
        index_models = importlib.import_module(f"{index}.models")
        index_config = importlib.import_module(f"{index}.config")
    except Exception as e:
        logger.exception(e)

    for _model in [*index_config.MODELS, "TransactionLog"]:
        getattr(index_models, _model).objects.all().delete()


def clear_all():

    models.Environment.objects.all().delete()
    models.Block.objects.all().delete()
    models.Txn.objects.all().delete()
    models.EventName.objects.all().delete()
    models.Contract.objects.all().delete()

    for index in INDEXERS_TO_SCAN:
        clear(index)
