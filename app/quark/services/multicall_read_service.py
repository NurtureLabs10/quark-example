"""
Support for MakerDAO MultiCall contract
"""
import logging
from dataclasses import dataclass
from typing import Any, List, Optional, Sequence, Tuple

from eth_abi.exceptions import DecodingError
from eth_account.signers.local import LocalAccount
from eth_typing import BlockIdentifier, BlockNumber, ChecksumAddress
from hexbytes import HexBytes
from web3 import Web3
from web3._utils.abi import map_abi_data
from web3._utils.normalizers import BASE_RETURN_NORMALIZERS
from web3.contract import ContractFunction
from .web3_service import Contract
from ..config import Environment

logger = logging.getLogger(__name__)


@dataclass
class MulticallResult:
    success: bool
    return_data: Optional[bytes]


@dataclass
class MulticallDecodedResult:
    success: bool
    return_data_decoded: Optional[Any]


class Multicall:
    ADDRESSES = {
        Environment.mainnet:	"0x41263cba59eb80dc200f3e2544eda4ed6a90e76c",
        Environment.testnet:	"0xae11C5B5f29A6a25e955F0CB8ddCc416f522AF5C",
        Environment.polygon_testnet:	"0xa1D6a0B3bE26FA898340b53d130FaAc855B87545",
        Environment.avalanche_testnet:	"0x3525056b441957683c646e60f155A5db6390144F",
        Environment.avalanche_mainnet: "0x115452aF3dD96809F61777010215219B8B30819D",
        Environment.fantom_testnet:	"0x0f0142450b65E562dbe871975da7ED0974e20D0e",
        Environment.arbitrum_testnet:	"0x06601d941386BA24575EE8A4Ec7E2E8cc7d81A1A",
        Environment.ropsten:	"0x53c43764255c17bd724f74c4ef150724ac50a3ed",
        Environment.aurora_test:	"0xE0F5c16d1f6FdC77C8e32eA22e56f115310ec61e",
    }

    def __init__(self, environment: Environment = Environment.mainnet) -> None:
        self.contract = Contract(
            contract_address=self.ADDRESSES[environment],
            environment=environment,
            abi_path='MultiCallGnosis.json'
        )
        self.w3 = self.contract.web3

    @staticmethod
    def _build_payload(
        contract_functions: Sequence[ContractFunction],
    ) -> Tuple[List[Tuple[ChecksumAddress, bytes]], List[List[Any]]]:
        targets_with_data = []
        output_types = []
        for contract_function in contract_functions:
            targets_with_data.append(
                (
                    contract_function.address,
                    HexBytes(contract_function._encode_transaction_data()),
                )
            )
            output_types.append(
                [output["type"] for output in contract_function.abi["outputs"]]
            )

        return targets_with_data, output_types

    def _decode_data(self, output_type: Sequence[str], data: bytes) -> Optional[Any]:
        """
        :param output_type:
        :param data:
        :return:
        :raises: DecodingError
        """
        if data:
            try:
                decoded_values = self.w3.codec.decode_abi(output_type, data)
                normalized_data = map_abi_data(
                    BASE_RETURN_NORMALIZERS, output_type, decoded_values
                )
                if len(normalized_data) == 1:
                    return normalized_data[0]
                else:
                    return normalized_data
            except DecodingError:
                logger.warning(
                    "Cannot decode %s using output-type %s", data, output_type
                )
                return data

    def _aggregate(
        self,
        targets_with_data: Sequence[Tuple[ChecksumAddress, bytes]],
        block_identifier: Optional[BlockIdentifier] = "latest",
    ) -> Tuple[BlockNumber, List[Optional[Any]]]:
        """
        :param targets_with_data: List of target `addresses` and `data` to be called in each Contract
        :param block_identifier:
        :return:
        :raises: BatchCallFunctionFailed
        """
        aggregate_parameter = [
            {"target": target, "callData": data} for target, data in targets_with_data
        ]
        return self.contract.read("aggregate", aggregate_parameter)

    def aggregate(
        self,
        contract_functions: Sequence[ContractFunction],
        block_identifier: Optional[BlockIdentifier] = "latest",
    ) -> Tuple[BlockNumber, List[Optional[Any]]]:
        """
        Calls ``aggregate`` on MakerDAO's Multicall contract. If a function called raises an error execution is stopped
        :param contract_functions:
        :param block_identifier:
        :return: A tuple with the ``blockNumber`` and a list with the decoded return values
        :raises: BatchCallFunctionFailed
        """
        targets_with_data, output_types = self._build_payload(
            contract_functions)
        block_number, results = self._aggregate(
            targets_with_data, block_identifier=block_identifier
        )
        decoded_results = [
            self._decode_data(output_type, data)
            for output_type, data in zip(output_types, results)
        ]

        return decoded_results
