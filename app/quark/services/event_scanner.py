import sys
import json
import importlib
from web3 import Web3
from web3.providers.rpc import HTTPProvider
from web3.middleware import geth_poa_middleware
from pipe import select, chain, dedup, sort, where, concat
from django.db.models import Max
from texttable import Texttable
# We use tqdm library to render a nice progress bar in the console
# https://pypi.org/project/tqdm/
from tqdm import tqdm
import pandas as pd
import logging
import datetime
import time
from abc import ABC, abstractmethod
from typing import Tuple, Optional, Callable, List, Iterable

from web3 import Web3
from web3.contract import Contract
from web3.datastructures import AttributeDict
from web3.exceptions import BlockNotFound
from eth_abi.codec import ABICodec
from ..config import CHAIN

# Currently this method is not exposed over official web3 API,
# but we need it to construct eth_getLogs parameters
from web3._utils.filters import construct_event_filter_params
from web3._utils.events import get_event_data

logger = logging.getLogger(__name__)

def log_table(data, columns):
    table = Texttable()
    # table.set_cols_align(["l", "r", "c"])
    # table.set_cols_valign(["t", "m", "b"])
    fields = columns
    display_names = list(
        fields
        | select(
            lambda column_name: (
                column_name.split('_')
                | select(
                    lambda x: x.title()
                )
                | concat(' ')
            )
        )
    )
    rows = [
        display_names,
        *list(
            data
            | select(lambda evt: [evt[f] for f in fields])
        )
    ]
    table.set_deco(Texttable.HEADER)
    table.add_rows(rows)
    logger.info(f"\n{table.draw()}")

def update_events(contracts, index):
    logger.info("Starting the event scan for following contracts...")

    log_table(
        list(
            contracts
            | select(
                lambda x: {
                    "contract_address": f"{x.contract_address[:7]}..{x.contract_address[-7:]}",
                    "environment": x.environment,
                    "abi_path": x.abi_path.split('.')[0]
                }
            )
        ),
        ['contract_address', 'environment', 'abi_path']
    )

    provider = HTTPProvider(contracts[0].chain['provider'])

    # Remove the default JSON-RPC retry middleware
    # as it correctly cannot handle eth_getLogs block range
    # throttle down.
    provider.middlewares.clear()

    web3 = Web3(provider)
    web3.middleware_onion.inject(geth_poa_middleware, layer=0)

    # Restore/create our persistent state
    state = DBState(contracts, index)

    # chain_id: int, web3: Web3, abi: dict, state: EventScannerState, events: List, filters: {}, max_chunk_scan_size: int=10000
    scanner = EventScanner(
        web3=web3,
        state=state,
        contracts=contracts,
        # How many maximum blocks at the time we request from JSON-RPC
        # and we are unlikely to exceed the response size limit of the JSON-RPC server
        max_chunk_scan_size=contracts[0].chain["max_chunk_scan_size"]
    )

    # # Assume we might have scanned the blocks all the way to the last Ethereum block
    # # that mined a few seconds before the previous scan run ended.
    # # Because there might have been a minor Etherueum chain reorganisations
    # # since the last scan ended, we need to discard
    # # the last few blocks from the previous scan results.
    # chain_reorg_safety_blocks = 10
    # scanner.delete_potentially_forked_block_data(state.get_last_scanned_block() - chain_reorg_safety_blocks)

    # # Scan from [last block scanned] - [latest ethereum block]
    # # Note that our chain reorg safety blocks cannot go negative
    # start_block = max(state.get_last_scanned_block() - chain_reorg_safety_blocks, 0)

    start_block = max(state.get_last_scanned_block(), 0)
    end_block = scanner.get_suggested_scan_end_block()
    blocks_to_scan = end_block - start_block

    logger.info(f"Scanning events for blocks: {start_block}-{end_block}")

    # Render a progress bar in the console
    start = time.time()

    # Run the scan
    result, total_chunks_scanned = scanner.scan(start_block, end_block)

    state.save()
    duration = time.time() - start
    logger.info(
        f"Scanned total {len(result)} events, in {duration} seconds, total {total_chunks_scanned} chunk scans performed"
    )


"""A stateful event scanner for Ethereum-based blockchains using Web3.py.

With the stateful mechanism, you can do one batch scan or incremental scans,
where events are added wherever the scanner left off.
"""


class EventScannerState(ABC):
    """Application state that remembers what blocks we have scanned in the case of crash.
    """

    @abstractmethod
    def get_last_scanned_block(self) -> int:
        """Number of the last block we have scanned on the previous cycle.

        :return: 0 if no blocks scanned yet
        """

    @abstractmethod
    def start_chunk(self, block_number: int):
        """Scanner is about to ask data of multiple blocks over JSON-RPC.

        Start a database session if needed.
        """

    @abstractmethod
    def end_chunk(self, block_number: int):
        """Scanner finished a number of blocks.

        Persistent any data in your state now.
        """

    @abstractmethod
    def process_event(self, block_when: datetime.datetime, event: AttributeDict) -> object:
        """Process incoming events.

        This function takes raw events from Web3, transforms them to your application internal
        format, then saves them in a database or some other state.

        :param block_when: When this block was mined

        :param event: Symbolic dictionary of the event data

        :return: Internal state structure that is the result of event tranformation.
        """

    # @abstractmethod
    # def delete_data(self, since_block: int) -> int:
    #     """Delete any data since this block was scanned.

    #     Purges any potential minor reorg data.
    #     """


class EventScanner:
    """Scan blockchain for events and try not to abuse JSON-RPC API too much.

    Can be used for real-time scans, as it detects minor chain reorganisation and rescans.
    Unlike the easy web3.contract.Contract, this scanner can scan events from multiple contracts at once.
    For example, you can get all transfers from all tokens in the same scan.

    You *should* disable the default `http_retry_request_middleware` on your provider for Web3,
    because it cannot correctly throttle and decrease the `eth_getLogs` block number range.
    """

    def __init__(self, web3: Web3, state: EventScannerState, contracts,
                 max_chunk_scan_size: int = 5000, max_request_retries: int = 30, request_retry_seconds: float = 3.0):
        """
        :param contract: Contract
        :param events: List of web3 Event we scan
        :param filters: Filters passed to getLogscontract_mapping
        :param max_chunk_scan_size: JSON-RPC API limit in the number of blocks we query. (Recommendation: 10,000 for mainnet, 500,000 for testnets)
        :param max_request_retries: How many times we try to reattempt a failed JSON-RPC call
        :param request_retry_seconds: Delay between failed requests to let JSON-RPC server to recover
        """

        self.logger = logger
        self.web3 = web3
        self.state = state
        self.contracts = contracts
        self.chain = CHAIN[self.contracts[0].environment]

        self.contract_mapping = dict(
            contracts
            | select(
                lambda _contract: (_contract.contract_address, _contract)
            )
        )

        def get_filters(_contract):
            return list(
                _contract.get_all_event_names()
                | select(lambda event_name: _contract.get_topic(event_name))
            )

        self.topics = list(
            contracts
            | select(get_filters)
            | chain
            | dedup
        )

        # self.filters={
        #     "address": list(
        #         contracts
        #         | select(lambda contract: contract.contract_address)
        #     )
        # }

        # Our JSON-RPC throttling parameters
        self.min_scan_chunk_size = 1000  # 12 s/block = 120 seconds period
        self.max_scan_chunk_size = max_chunk_scan_size
        self.max_request_retries = max_request_retries
        self.request_retry_seconds = request_retry_seconds

        # Factor how fast we increase the chunk size if results are found
        # # (slow down scan after starting to get hits)
        self.chunk_size_decrease = 0.5

        # Factor how was we increase chunk size if no results found
        self.chunk_size_increase = 2.0

    @property
    def address(self):
        return self.token_address

    def get_block_timestamp(self, block_num) -> datetime.datetime:
        """Get Ethereum block timestamp"""
        try:
            block_info = self.web3.eth.getBlock(block_num)
        except BlockNotFound:
            # Block was not mined yet,
            # minor chain reorganisation?
            return None
        last_time = block_info["timestamp"]
        return datetime.datetime.utcfromtimestamp(last_time)

    def get_suggested_scan_start_block(self):
        """Get where we should start to scan for new token events.

        If there are no prior scans, start from block 1.
        Otherwise, start from the last end block minus ten blocks.
        We rescan the last ten scanned blocks in the case there were forks to avoid
        misaccounting due to minor single block works (happens once in a hour in Ethereum).
        These heurestics could be made more robust, but this is for the sake of simple reference implementation.
        """

        end_block = self.get_last_scanned_block()
        if end_block:
            return max(end_block, self.chain['min_block_number'])
        return 1

    def get_suggested_scan_end_block(self):
        """Get the last mined block on Ethereum chain we are following."""

        # Do not scan all the way to the final block, as this
        # block might not be mined yet
        # return self.web3.eth.blockNumber - 1
        return self.web3.eth.blockNumber

    def get_last_scanned_block(self) -> int:
        return self.state.get_last_scanned_block()

    # def delete_potentially_forked_block_data(self, after_block: int):
    #     """Purge old data in the case of blockchain reorganisation."""
    #     self.state.delete_data(after_block)

    def scan_chunk(self, start_block, end_block) -> Tuple[int, datetime.datetime, list]:
        """Read and process events between to block numbers.

        Dynamically decrease the size of the chunk if the case JSON-RPC server pukes out.

        :return: tuple(actual end block number, when this block was mined, processed events)
        """

        block_timestamps = {}
        get_block_timestamp = self.get_block_timestamp

        # Cache block timestamps to reduce some RPC overhead
        # Real solution might include smarter models around block
        def get_block_when(block_num):
            if block_num not in block_timestamps:
                block_timestamps[block_num] = get_block_timestamp(block_num)
            return block_timestamps[block_num]

        all_processed = []

        for topic in self.topics:
            # logger.info(f"Scanning topic {topic}")
            # Callable that takes care of the underlying web3 call
            def _fetch_events(_start_block, _end_block):
                return _fetch_events_for_all_contracts(
                    self.web3,
                    topic,
                    self.contract_mapping,
                    from_block=_start_block,
                    to_block=_end_block
                )

            # Do `n` retries on `eth_getLogs`,
            # throttle down block range if needed
            end_block, events = _retry_web3_call(
                _fetch_events,
                start_block=start_block,
                end_block=end_block,
                retries=self.max_request_retries,
                delay=self.request_retry_seconds
            )

            for evt in events:
                # Integer of the log index position in the block, null when its pending
                idx = evt["logIndex"]

                # We cannot avoid minor chain reorganisations, but
                # at least we must avoid blocks that are not mined yet
                assert idx is not None, "Somehow tried to scan a pending block"

                block_number = evt["blockNumber"]

                # Get UTC time when this event happened (block mined timestamp)
                # from our in-memory cache
                block_when = get_block_when(block_number)

                processed = self.state.process_event(block_when, evt)
                all_processed.append(processed)

        end_block_timestamp = get_block_when(end_block)
        return end_block, end_block_timestamp, all_processed

    def estimate_next_chunk_size(self, current_chuck_size: int, event_found_count: int):
        """Try to figure out optimal chunk size

        Our scanner might need to scan the whole blockchain for all events

        * We want to minimize API calls over empty blocks

        * We want to make sure that one scan chunk does not try to process too many entries once, as we try to control commit buffer size and potentially asynchronous busy loop

        * Do not overload node serving JSON-RPC API by asking data for too many events at a time

        Currently Ethereum JSON-API does not have an API to tell when a first event occurred in a blockchain
        and our heuristics try to accelerate block fetching (chunk size) until we see the first event.

        These heurestics exponentially increase the scan chunk size depending on if we are seeing events or not.
        When any transfers are encountered, we are back to scanning only a few blocks at a time.
        It does not make sense to do a full chain scan starting from block 1, doing one JSON-RPC call per 20 blocks.
        """

        if event_found_count > 0:
            # When we encounter first events, reset the chunk size window
            current_chuck_size *= self.chunk_size_increase
        else:
            current_chuck_size *= self.chunk_size_increase

        current_chuck_size = max(self.min_scan_chunk_size, current_chuck_size)
        current_chuck_size = min(self.max_scan_chunk_size, current_chuck_size)
        return int(current_chuck_size)

    def scan(self, start_block, end_block, progress_callback=Optional[Callable]) -> Tuple[
            list, int]:
        """Perform a token balances scan.

        Assumes all balances in the database are valid before start_block (no forks sneaked in).

        :param start_block: The first block included in the scan

        :param end_block: The last block included in the scan

        :param start_chunk_size: How many blocks we try to fetch over JSON-RPC on the first attempt

        :param progress_callback: If this is an UI application, update the progress of the scan

        :return: [All processed events, number of chunks used]
        """

        assert start_block <= end_block

        current_block = start_block

        # Scan in chunks, commit between
        chunk_size = self.max_scan_chunk_size
        last_scan_duration = last_logs_found = 0
        total_chunks_scanned = 0

        # All processed entries we got on this scan cycle
        all_processed = []

        while current_block <= end_block:

            self.state.start_chunk(current_block, chunk_size)

            # Print some diagnostics to logs to try to fiddle with real world JSON-RPC API performance
            estimated_end_block = min(current_block + chunk_size, end_block)
            logger.info(
                f"{'-' * 80}\n"
                f"Scanning events for blocks: {current_block}-{estimated_end_block}\n"
                f"chunk_size: {estimated_end_block - current_block}\n"
                f"last_chunk_scan took: {round(last_scan_duration, 2)}"
                # f"last logs found {last_logs_found}"
            )

            start = time.time()
            actual_end_block, end_block_timestamp, new_entries = self.scan_chunk(
                current_block,
                estimated_end_block
            )

            # logger.info("Found the following entries...")
            # for entry in new_entries:
            #     logger.info(entry)

            # Where does our current chunk scan ends - are we out of chain yet?
            current_end = actual_end_block

            last_scan_duration = time.time() - start
            all_processed += new_entries

            # Try to guess how many blocks to fetch over `eth_getLogs` API next time
            chunk_size = self.estimate_next_chunk_size(
                chunk_size, len(new_entries))

            # Set where the next chunk starts
            current_block = current_end + 1
            total_chunks_scanned += 1
            self.state.end_chunk(current_end)

        return all_processed, total_chunks_scanned


def _retry_web3_call(func, start_block, end_block, retries, delay) -> Tuple[int, list]:
    """A custom retry loop to throttle down block range.

    If our JSON-RPC server cannot serve all incoming `eth_getLogs` in a single request,
    we retry and throttle down block range for every retry.

    For example, Go Ethereum does not indicate what is an acceptable response size.
    It just fails on the server-side with a "context was cancelled" warning.

    :param func: A callable that triggers Ethereum JSON-RPC, as func(start_block, end_block)
    :param start_block: The initial start block of the block range
    :param end_block: The initial start block of the block range
    :param retries: How many times we retry
    :param delay: Time to sleep between retries
    """
    for i in range(retries):
        try:
            return end_block, func(start_block, end_block)
        except Exception as e:
            # Assume this is HTTPConnectionPool(host='localhost', port=8545): Read timed out. (read timeout=10)
            # from Go Ethereum. This translates to the error "context was cancelled" on the server side:
            # https://github.com/ethereum/go-ethereum/issues/20426
            if i < retries - 1:
                # Give some more verbose info than the default middleware
                logger.warning(
                    "Retrying events for block range %d - %d (%d) failed with %s, retrying in %s seconds",
                    start_block,
                    end_block,
                    end_block-start_block,
                    e,
                    delay)
                # Decrease the `eth_getBlocks` range
                end_block = start_block + ((end_block - start_block) // 2)
                # Let the JSON-RPC to recover e.g. from restart
                time.sleep(delay)
                continue
            else:
                logger.warning("Out of retries")
                raise


def get_event_abi(contract_mapping, topic0, address):
    contract_instance = contract_mapping.get(
        address.lower()) or contract_mapping.get(address)
    return contract_instance.get_abi_for_topic(topic0)


def decode_log(web3, contract_mapping, log):
    topic0 = log['topics'][0]
    address = log['address']
    decoded_event = get_event_data(
        web3.codec,
        get_event_abi(contract_mapping, topic0, address),
        log
    )
    # decoded_event = dict(decoded_event)
    # args = decoded_event.pop('args')
    # decoded_event.update(args)
    return decoded_event


def _fetch_events_for_all_contracts(
        web3,
        topic,
        contract_mapping,
        from_block: int,
        to_block: int) -> Iterable:
    """Get events using eth_getLogs API.

    This method is detached from any contract instance.

    This is a stateless method, as opposed to createFilter.
    It can be safely called against nodes which do not provide `eth_newFilter` API, like Infura.
    """

    address_list = list(
        contract_mapping.values()
        | select(lambda contract: contract.contract_address)
    )

    if from_block is None:
        raise TypeError(
            "Missing mandatory keyword argument to getLogs: fromBlock")

    event_filter_params = {
        'topics': [topic],
        'address': address_list,
        'fromBlock': from_block,
        'toBlock': to_block
    }

    logger.debug(
        "Querying eth_getLogs with the following parameters: %s", event_filter_params)

    all_events = list(
        web3.eth.get_logs(event_filter_params)
        | select(lambda log: decode_log(web3, contract_mapping, log))
    )

    return all_events


class DBState(EventScannerState):
    """
    Store the state of scanned blocks and all events.

    All state is an in-memory dict.
    Simple load/store massive JSON on start up.
    """

    def __init__(self, contracts, index):
        self.contracts = contracts
        self.environment = contracts[0].environment
        self.state = []
        self.index = index

        self.logs = None
        try:
            self.logs = importlib.import_module(
                f"{index}.models").TransactionLog
        except (ModuleNotFoundError, AttributeError) as e:
            # logger.warning(f"{app_name}: No contracts to track")
            pass
        except Exception as e:
            logger.exception(e)

    def clear(self):
        self.state = []

    def save(self):
        """Save everything we have scanned so far to the db."""

        contract_mapping = dict(
            self.contracts
            | select(
                lambda _contract: (_contract.contract_address, _contract)
            )
        )

        # Remove the pre-saved events
        def get_reference_key(_event):
            return f"{self.environment}-{_event['block_number']}-{_event['transaction_index']}-{_event['log_index']}"

        reference_keys = list(
            self.state
            | select(get_reference_key)
        )

        saved_reference_keys = list(
            self.logs.objects
            .filter(reference_key__in=reference_keys)
            .values_list("reference_key", flat=True)
        )

        events_to_save = list(
            self.state
            | where(
                lambda _event: get_reference_key(
                    _event) not in saved_reference_keys
            )
            | sort(
                key=lambda _event: (
                    _event['block_number'],
                    _event['transaction_index'],
                    _event['log_index']
                )
            )
        )
        
        if events_to_save:

            logger.info(f"Processing {len(events_to_save)} event...")
            log_table(events_to_save, ['event_name', 'block_number', 'transaction_index', 'log_index'])

        for event in events_to_save:
            contract_instance = contract_mapping.get(
                event["address"].lower()
            ) or contract_mapping.get(event["address"])
            contract_instance.process_and_save(event)
    #
    # EventScannerState methods implemented below
    #

    def get_last_scanned_block(self):
        """The number of the last block we have stored."""
        self.chain = CHAIN[self.contracts[0].environment]

        end_block = self.logs.objects\
            .filter(
                contract__address__in=list(
                    self.contracts
                    | select(lambda contract: contract.contract_address)
                ),
                txn__block__environment__environment=self.contracts[0].environment
            )\
            .aggregate(max_block_number=Max('txn__block__block_number'))\
            .pop('max_block_number')

        if end_block:
            return max(end_block, self.chain['min_block_number'])

        if self.chain['min_block_number']:
            return self.chain['min_block_number']

        return 1

    # def delete_data(self, since_block):
    #     """Remove potentially reorganised blocks from the scan data."""
    #     for block_num in range(since_block, self.get_last_scanned_block()):
    #         if block_num in self.state["blocks"]:
    #             del self.state["blocks"][block_num]

    def start_chunk(self, block_number, chunk_size):
        self.clear()

    def end_chunk(self, block_number):
        """Save at the end of each chunk, so we can resume in the case of a crash or CTRL+C"""
        self.save()
        self.clear()

    def process_event(self, block_when: datetime.datetime, event: AttributeDict) -> str:
        """Save the events in a local state to be saved to the DB at the end of this chunk"""

        log_index = event.logIndex  # Log index within the block
        txhash = event.transactionHash.hex()  # Transaction hash
        block_number = event.blockNumber

        # Convert ERC-20 Transfer event to our internal format

        event_data = {
            "event_name": event.event,
            "timestamp": block_when,
            "log_index": log_index,
            "transaction_index": event.transactionIndex,
            "txhash": txhash,
            "block_number": block_number,
            "address": event.address,
            "args": event["args"]
        }

        self.state.append(event_data)

        # Return a pointer that allows us to look up this event later if needed
        return f"{block_number}-{txhash}-{log_index}"
