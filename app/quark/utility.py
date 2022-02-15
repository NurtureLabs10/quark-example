import math
from datetime import datetime
from .contract import get_checksum_address
from . import config
from web3 import Web3
from typing import Optional
from pipe import select,  where


def change_case(str):
    return ''.join(['_'+i.lower() if i.isupper()
                    else i for i in str]).lstrip('_')


def round_(x, div_by=18):
    try:
        return round(int(x)/math.pow(10, div_by), div_by)
    except ValueError as e:
        print(x)
        raise e


def to_date_components(timestamp: str):
    difference = datetime.fromtimestamp(
        int(timestamp)) - datetime.now()
    days = difference.days
    seconds = difference.seconds
    hours = seconds//3600
    return days, hours


def _amount(x):
    return round_(x)


def _price(x):
    return round(
        round_(x, 8),
        2
    )


def bnb_balance(address, environment=config.Environment.mainnet):
    chain = config.CHAIN[environment]
    address = Web3.toChecksumAddress(address)
    return round(
        Web3(
            Web3.HTTPProvider(chain['provider'])
        ).eth.getBalance(address)/1e18, 2
    )


def are_addresses_equal(address1: Optional[str] = None, address2: Optional[str] = None):

    def f(address):
        return get_checksum_address(address) if address else address

    return f(address1) == f(address2)


def get_chains(environment):
    environments = list(
        config.CHAIN
        | where(lambda x: config.CHAIN[x]['chain_type'] == environment)
        | select(lambda x: x.value)
    )
    return environments
