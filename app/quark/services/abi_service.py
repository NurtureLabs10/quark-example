from json.decoder import JSONDecodeError
import requests
from .. import config
import json
import os
from typing import Optional
import time
import logging
import diskcache as dc
import requests

logger = logging.getLogger(__name__)
cache = dc.Cache('tmp')

def get_abi(contract_address: str, environment: str = "testnet", abi_path: Optional[str] = None):
    if abi_path:
        # logger.info("Getting ABI from file")
        dirname = os.path.dirname(__file__)
        filename = os.path.join(dirname, f"../abis/{abi_path}")
        f = open(filename, 'r')
        abi = json.load(f)
        return abi
    # logger.info("No ABI found, fetching it")
    return fetch_abi(contract_address, environment)


@cache.memoize()
def call_bsc(url):
    r = requests.get(url)

    try:
        result = r.json()['result']
    except JSONDecodeError as e:
        print(r.text)
        raise e

    retry_period = 2
    while result == 'Max rate limit reached':
        time.sleep(retry_period)
        r = requests.get(url)
        result = r.json()['result']
        retry_period += retry_period/2
    return result


@cache.memoize()
def fetch_abi(contract_address, environment):
    # logger.info("Fetch")
    chain = config.CHAIN[environment]
    # logger.info(chain['explorer_api'])
    url = f"https://{chain['explorer_api']}/api?module=contract&action=getabi&address={contract_address}&apikey={chain['explorer_key']}"
    # logger.info(url)
    abi = call_bsc(url)
    # logger.info("fetch_abi")
    # logger.info(abi)
    return None if abi == "Contract source code not verified" else abi
