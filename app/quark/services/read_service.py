from itertools import cycle
from web3 import Web3
from .. import config
from web3.middleware import geth_poa_middleware
from requests import HTTPError
import logging
import diskcache as dc
from common.utils.encryption_utils import hash_password
from common.exceptions import NotAcceptableError
from common.timeit import timeit

logger = logging.getLogger(__name__)
cache = dc.Cache('tmp')
READ_CACHE_TIME = 7


def get_read_balance_cache_key(*args, **kwargs):
    signature = f"{kwargs}{args}"
    return hash_password(signature)


def get_read_cache_key(contract_address, environment, abi, function_name, *args, **kwargs):
    default_block = 'latest'
    if "default_block" in kwargs:
        default_block = kwargs["default_block"]
    signature = f"{contract_address}{environment}{function_name}{default_block}{args}"
    k = hash_password(signature)
    # logger.info(f"general {signature}: {k}")
    return k


@cache.memoize(expire=READ_CACHE_TIME)
def read_balance(contract_address, environment, abi):

    contract_address = Web3.toChecksumAddress(contract_address)

    def get_web3_instance(provider):
        web3 = Web3(Web3.HTTPProvider(provider))
        web3.middleware_onion.inject(geth_poa_middleware, layer=0)
        return web3

    logger.info(f"fetching balance: {contract_address}")
    max_retries = 15
    try_count = 0

    all_providers = get_all_providers(environment)

    for provider in cycle(all_providers):
        try:
            try_count += 1
            logger.info(f"provider: {provider}")
            result = get_web3_instance(
                provider).eth.getBalance(contract_address)
            logger.info(f"balance: {contract_address}, result: {result}")

            # Save the result in a permanent cache and then if all the retries are over then return the permanent cached result
            set_permanent_cache(
                result,
                contract_address,
                environment,
                abi,
                "getWeb3Balance"
            )

            # Note down this provider and try this as the first provider in the next call
            set_working_provider(environment, provider)

            return result
        except HTTPError as e:
            if try_count >= max_retries:
                return get_permanent_cache(contract_address, environment, abi, "getWeb3Balance")
            print(
                f'Trying again, retry number: {try_count}, switching providers'
            )


read_balance.__cache_key__ = get_read_balance_cache_key


@cache.memoize(expire=READ_CACHE_TIME)
@timeit
def read(contract_address, environment, abi, function_name, default_block, *args):

    contract_address = Web3.toChecksumAddress(contract_address)

    def get_web3(provider):
        web3 = Web3(Web3.HTTPProvider(provider))
        web3.middleware_onion.inject(geth_poa_middleware, layer=0)
        return web3

    def get_contract_instance(provider, default_block):
        web3 = get_web3(provider)
        web3.eth.defaultBlock = default_block;
        return web3.eth.contract(
            address=contract_address,
            abi=abi
        )

    log_dump = f"Read Call: {contract_address}, {environment}, {default_block}, {function_name}, {args}"
    logger.info(
        log_dump if len(log_dump) < 200 else f"{log_dump[:200]}..." 
    )
    # logger.info(f"fetching function_name: {function_name}, args: {args}")
    max_retries = 15
    try_count = 0

    all_providers = get_all_providers(environment)

    for provider in cycle(all_providers):
        try:
            try_count += 1
            # logger.info(f"provider: {provider}")
            result = getattr(
                get_contract_instance(provider, default_block).functions,
                function_name
            )(*args).call()

            # logger.info(
            #     f"function_name: {function_name}, args: {args}, result: {result}"
            # )

            # Save the result in a permanent cache and then if all the retries are over then return the permanent cached result
            set_permanent_cache(
                result,
                contract_address,
                environment,
                abi,
                function_name,
                *args,
                default_block=default_block
            )

            # Note down this provider and try this as the first provider in the next call
            set_working_provider(environment, provider)

            return result
        except HTTPError as e:
            if try_count >= max_retries:
                return get_permanent_cache(contract_address, environment, abi, function_name, *args)
            print(
                f'Trying again, retry number: {try_count}, switching providers'
            )


read.__cache_key__ = get_read_cache_key


def set_permanent_cache(result, *args, **kwargs):
    cache_key = get_read_cache_key(*args, **kwargs)
    cache_key = f"{cache_key}-permanent"
    cache.set(cache_key, result)


def get_permanent_cache(*args, **kwargs):
    cache_key = get_read_cache_key(*args, **kwargs)
    cache_key = f"{cache_key}-permanent"
    result = cache.get(cache_key)
    if result == None:
        raise NotAcceptableError(
            'Providers are not working at the moment, failing...')
    return result


def get_all_providers(environment):
    chain = config.CHAIN[environment]
    working_provider = get_working_provider(environment)
    working_providers = [working_provider, ] if working_provider else []
    return [
        *working_providers, chain['provider'], *chain['backup_providers']
    ]


def _get_working_provider_key(environment):
    return f'{environment}-working_provider'


def get_working_provider(environment):
    return cache.get(
        _get_working_provider_key(environment),
        None
    )


def set_working_provider(environment, provider):
    cache.set(
        _get_working_provider_key(environment),
        provider
    )


def save_result_in_cache(result, contract_address, environment, abi, function_name, *args, **kwargs):
    key = get_read_cache_key(
        contract_address, environment, abi, function_name, *args, **kwargs
    )
    # logger.info(f"Saving result in cache: {key}")
    cache.set(key, result, expire=READ_CACHE_TIME)
