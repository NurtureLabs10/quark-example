import pytz
import sha3
import importlib
from web3 import Web3
from .. import config

from web3.middleware import geth_poa_middleware
from typing import Optional
import time
from common.exceptions import NotAcceptableError
import logging
import diskcache as dc
from django.db.models.functions import Concat
from django.db.models import F, CharField
from hexbytes import HexBytes
from .read_service import read, read_balance
from .parse_service import parse
from .abi_service import get_abi
from pipe import select, where
from django.db import IntegrityError, transaction

logger = logging.getLogger(__name__)
cache = dc.Cache("tmp")


class Contract(object):
    def __init__(
        self,
        index: str,
        contract_address: str,
        environment: str = "testnet",
        abi_path: Optional[str] = None,
    ):
        self.contract_address = self.get_checksum_address(contract_address)
        self.environment = environment
        self.web3 = Web3(Web3.HTTPProvider(self.chain["provider"]))
        self.web3.middleware_onion.inject(geth_poa_middleware, layer=0)
        self.abi_path = abi_path
        self.abi = get_abi(contract_address, environment, abi_path)
        # logger.info(self.abi)
        self.contract_instance = self.web3.eth.contract(
            address=self.contract_address, abi=self.abi
        )
        self.callbacks = {}
        self.events_to_scan = None
        self.index = index

    def get_checksum_address(self, address):
        try:
            checksum_address = Web3.toChecksumAddress(address)
        except ValueError:
            raise NotAcceptableError(f"{address} is not valid")
        return checksum_address

    @property
    def balance(self):
        _balance = read_balance(self.contract_address, self.environment, self.abi)
        return round(_balance / 1e18, 2)

    @property
    def chain(self):
        return config.CHAIN[self.environment]

    def _get_nonce(self):
        nonce = self.web3.eth.getTransactionCount(
            Web3.toChecksumAddress(self.chain["address"])
        )
        return nonce

    def write(self, function_name: str, *args):
        return self.publish_txn(
            getattr(self.contract_instance.functions, function_name)(*args)
        )

    def f(self, function_name, *args):
        return getattr(self.contract_instance.functions, function_name)(*args)

    def publish_txn(self, transfer_txn):
        nonce = self._get_nonce()
        gas_price = config.CHAIN[self.environment]["gas_price"]

        transfer_txn = transfer_txn.buildTransaction(
            {
                "chainId": self.chain["chain_id"],
                "gas": 500000,
                "gasPrice": self.web3.toWei(str(gas_price), "gwei"),
                "nonce": nonce,
            }
        )

        signed_txn = self.web3.eth.account.sign_transaction(
            transfer_txn, private_key=self.chain["private_key"]
        )

        self.web3.eth.sendRawTransaction(signed_txn.rawTransaction)

        txn_hash = self.web3.toHex(Web3.keccak(signed_txn.rawTransaction))
        print(f"View txn at https://{self.chain['explorer']}/tx/{txn_hash}")

        new_nonce = self._get_nonce()
        while new_nonce == nonce:
            time.sleep(2)
            new_nonce = self._get_nonce()

        return txn_hash

    def read(self, function_name: str, *args, default_block="latest"):
        return read(
            self.contract_address,
            self.environment,
            self.abi,
            function_name,
            default_block,
            *args,
        )

    def add_callbacks(self, callbacks={}):
        if callbacks and isinstance(callbacks, dict):
            self.callbacks = callbacks

    def execute_callback(self, event):
        if event["event_name"] in self.callbacks:
            event = self.callbacks[event["event_name"]](event, self)
        return event

    def process_and_save(self, event):
        """
        eg. event = {
            "event_name": event_name,
            "timestamp": block_when,
            "log_index": log_index,
            "transaction_index": transaction_index,
            "txhash": txhash,
            "block_number": block_number,
            "address": event.address,
            "args": event["args"]
        }
        """
        # logger.info(f"Saving events for {self}")

        try:
            with transaction.atomic():
                event = self.execute_callback(event)
                self.save_event(event)
        except Exception as e:
            logger.exception(e)

    @property
    def _index_models(self):
        attr_name = "index_models"
        if hasattr(self, attr_name):
            return getattr(self, attr_name)
        try:
            setattr(self, attr_name, importlib.import_module(f"{self.index}.models"))
        except (ModuleNotFoundError, AttributeError) as e:
            # logger.warning(f"{app_name}: No contracts to track")
            pass
        except Exception as e:
            logger.exception(e)

        return getattr(self, attr_name)

    def save_event(self, event):
        event = parse(event)

        block, _ = self._index_models.Block.objects.get_or_create(
            timestamp=pytz.utc.localize(event["timestamp"]),
            block_number=event["block_number"],
            environment=self.evironment_db_object,
        )

        txn, _ = self._index_models.Txn.objects.get_or_create(
            block=block, hash=event["txhash"], index=event["transaction_index"]
        )

        event_name, _ = self._index_models.EventName.objects.get_or_create(
            event_name=event["event_name"]
        )

        # logger.info(f"event_name {event_name.id} {event_name.event_name}")

        self._index_models.TransactionLog.objects.create(
            txn=txn,
            contract=self.contract_db_object,
            event_name=event_name,
            log_index=event["log_index"],
            data=event["args"],
            reference_key=f"{block.environment.environment}-{block.block_number}-{txn.index}-{event['log_index']}",
        )

    def get_abi_for_topic(self, topic0):
        if isinstance(topic0, HexBytes):
            topic0 = topic0.hex()
        if hasattr(self, "topic_to_abi_mapping"):
            return self.topic_to_abi_mapping[topic0]
        self.topic_to_abi_mapping = dict(
            list(
                self.get_all_event_names()
                | select(
                    lambda event_name: (
                        self.get_topic(event_name),
                        self.get_event_abi(event_name),
                    )
                )
            )
        )
        return self.topic_to_abi_mapping[topic0]

    def get_unsaved_events(self, events):
        def _get_composite_key(event):
            return f"{str(event['transactionHash'])}{event['logIndex']}{event['event']}"

        mapped_events = {_get_composite_key(event): event for event in events}

        saved_event_keys = list(
            self.logs.annotate(
                composite_key=Concat(
                    F("hash"), F("log_index"), F("event_name"), output_field=CharField()
                )
            )
            .filter(composite_key__in=list(mapped_events.keys()))
            .values("composite_key")
        )

        unsaved_keys = list(set(list(mapped_events.keys())) - set(saved_event_keys))

        return [mapped_events[unsaved_key] for unsaved_key in unsaved_keys]

    def get_all_event_types(self):
        return list(
            self.get_all_event_names()
            | select(
                lambda event_name: getattr(self.contract_instance.events, event_name)
            )
        )

    def get_all_event_names(self):
        return list(
            self.contract_instance.abi
            | where(lambda x: x["type"] == "event")
            | select(lambda x: x["name"])
        )

    def get_event_abi(self, event_name):
        data = list(
            filter(lambda x: x.get("name") == event_name, self.contract_instance.abi)
        )
        if data:
            data = data[0]
        else:
            raise NotAcceptableError("Invalid Event Name")
        return data

    def get_topic(self, event_name):
        data = self.get_event_abi(event_name)
        message = f"{data['name']}({','.join(list(map(lambda x: x['type'], data['inputs'])))})"

        k = sha3.keccak_256()
        k.update(message.encode("utf-8"))
        return f"0x{k.hexdigest()}"

    @property
    def logs(self):
        return self._index_models.TransactionLog.objects.annotate(
            contract_address=F("contract__address"),
            environment=F("txn__block__environment__environment"),
            timestamp=F("txn__block__timestamp"),
            block_number=F("txn__block__block_number"),
            hash=F("txn__hash"),
            event=F("event_name__event_name"),
        ).filter(environment=self.environment, contract_address=self.contract_address)

    @property
    def evironment_db_object(self):
        if hasattr(self, "_evironment_db_object"):
            return self._evironment_db_object

        (
            self._evironment_db_object,
            _,
        ) = self._index_models.Environment.objects.get_or_create(
            environment=self.environment
        )

        return self._evironment_db_object

    @property
    def contract_db_object(self):
        if hasattr(self, "_contract_db_object"):
            return self._contract_db_object

        self._contract_db_object, _ = self._index_models.Contract.objects.get_or_create(
            address=self.contract_address, environment=self.evironment_db_object
        )
        return self._contract_db_object

    def __str__(self):
        return f"{self.contract_address} on {self.environment} with {self.abi_path}"

    def __repr__(self):
        return f"{self.contract_address} on {self.environment} with {self.abi_path}"
