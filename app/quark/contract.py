# Contract Registry
import importlib
from django.conf import settings
from .services import web3_service
from web3 import Web3
from quark.services.multicall_read_service import Multicall
from pipe import select, where
from .services.read_service import save_result_in_cache
from collections import defaultdict

import logging

logger = logging.getLogger(__name__)

ContractRegistryMap = defaultdict(lambda: defaultdict(dict))


def get_checksum_address(address):
    return Web3.toChecksumAddress(address)


def register(
    index, contract_address, environment, abi_path, callbacks={}, events_to_scan=[]
):
    contract_address = contract_address.lower()

    contract_instance = web3_service.Contract(
        index=index,
        contract_address=contract_address,
        environment=environment,
        abi_path=abi_path,
    )

    if callbacks:
        contract_instance.add_callbacks(callbacks)

    if events_to_scan:
        contract_instance.events_to_scan = events_to_scan

    ContractRegistryMap[index][environment][contract_address] = contract_instance


def get(index, contract_address, environment, abi_path=None):
    contract_address = contract_address.lower()
    try:
        return ContractRegistryMap[index][environment][contract_address]
    except KeyError as e:
        try:
            register(index, contract_address, environment, abi_path)
        except Exception as e:
            logger.error(
                f"Contract {contract_address} on {environment} couldn't be registered"
            )
    return ContractRegistryMap[index][environment][contract_address]


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


def register_all_contracts():

    index_apps = list(
        settings.CUSTOM_APPS | where(lambda _name: _name.startswith("index_"))
    )

    for app_name in index_apps:
        logger.info("*" * 10 + f"Registering Contracts in {app_name}" + "*" * 10)
        registry = []
        try:
            registry = importlib.import_module(
                f"{app_name}.contract_registry"
            ).get_registry()
        except (ModuleNotFoundError, AttributeError) as e:
            # logger.warning(f"{app_name}: No contracts to track")
            pass
        except Exception as e:
            logger.exception(e)

        for contract_details in registry:
            register(index=app_name, **contract_details)


def multicall(contract_functions, environment):
    m = Multicall(environment=environment)
    return m.aggregate(
        contract_functions
    )


def cached_multicall(calls, environment):
    results = multicall(
        list(
            calls
            | select(
                lambda x: get(
                    contract_address=x[0], abi_path=x[1], environment=environment
                ).f(x[2], *x[3:])
            )
        ),
        environment=environment,
    )

    for index, result in enumerate(results):
        contract_address = calls[index][0]
        abi_path = calls[index][1]
        save_result_in_cache(
            result,
            contract_address,
            environment,
            abi_path,
            calls[index][2],
            *calls[index][3:],
        )
    return results
