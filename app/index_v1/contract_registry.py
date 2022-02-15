from . import config
from .services.update_token_holders_service import on_token_transfer
import logging

logger = logging.getLogger(__name__)


def get_registry():

    contract_registry = []

    for environment in config.TOKEN_CONTRACT:
        token_contract = config.TOKEN_CONTRACT[environment]
        contract_registry.append(
            {
                "contract_address": token_contract['address'],
                "environment": environment,
                "abi_path": token_contract['abi'],
                "callbacks": {
                    "Transfer": on_token_transfer
                }
            }
        )
    return contract_registry
