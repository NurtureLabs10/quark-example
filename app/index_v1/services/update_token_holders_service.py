from ..models import TokenBalance
import logging
logger = logging.getLogger(__name__)


def on_token_transfer(event, contract_instance):
    logger.debug("Running on_token_transfer")
    TokenBalance.update_ledger(
        contract=contract_instance.contract_db_object,
        _from=event['args']['from'],
        _to=event['args']['to'],
        amount=event['args']['value']
    )
    return event
