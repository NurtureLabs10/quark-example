from fastapi import APIRouter
from common.decorators import catch_exception, close_db_connection
from quark.indexer import get_index_by_tag
from pipe import select
import logging
logger = logging.getLogger(__name__)

api_router = APIRouter()


@api_router.get("/balance/{account}/")
@catch_exception()
@close_db_connection()
def get_token_balances(account: str):
    balances_across_chains = get_index_by_tag('usdc_token').models.TokenBalance.objects.filter(account=account)
    if not balances_across_chains:
        return 0
    return sum(balances_across_chains | select(lambda x: x.balance)) 
