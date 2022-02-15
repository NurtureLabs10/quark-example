from enum import Enum
import os

ADDRESS_0 = "0x0000000000000000000000000000000000000000"


class AssetsKey(str, Enum):
    BNB = "BNB"
    BTC = "BTC"
    ETH = "ETH"
    TSLA = "TSLA"
    GOOGL = "GOOGL"
    AMZN = "AMZN"
    NFLX = "NFLX"
    GME = "GME"
    FB = "FB"
    NVDA = "NVDA"
    AAPL = "AAPL"
    SOL = "SOL"
    LINK = "LINK"
    XRP = "XRP"
    ADA = "ADA"
    MATIC = "MATIC"
    XAG = "XAG"
    XAU = "XAU"
    AVAX = "AVAX"
    FTM = "FTM"


class Environment(str, Enum):
    testnet = "testnet"
    mainnet = "mainnet"
    polygon_testnet = "mumbai-test"
    polygon_mainnet = "polygon-mainnet"
    avalanche_testnet = "fuji-test"
    avalanche_mainnet = "avalanche-mainnet"
    fantom_testnet = "fantom-test"
    arbitrum_testnet = "arbitrum-test"
    ropsten = "ropsten"
    aurora_test = "aurora-test"
    aurora_mainnet = "aurora-main"


class ChainType(str, Enum):
    testnet = "testnet"
    mainnet = "mainnet"


CHAIN = {
    Environment.mainnet: {
        # Set the min block based on the earliest creation blocks of all the contracts you are indexing
        "min_block_number": 11025908,
        "provider": "https://bsc-dataseed.binance.org/",
        "default_asset": AssetsKey.BNB,
        "gas_price": 10,
        "explorer_api": "api.bscscan.com",
        "explorer": "bscscan.com",
        "explorer_key": os.environ.get("BSCSCAN_KEY"),
        "chain_id": 56,
        "private_key": os.environ.get("MAINNET_PK"),
        "address": os.environ.get("MAINNET_ADDRESS"),
        "backup_providers": [
            "https://bsc-dataseed1.defibit.io/",
            "https://bsc-dataseed2.defibit.io/",
            "https://bsc-dataseed3.defibit.io/",
            "https://bsc-dataseed4.defibit.io/",
            "https://bsc-dataseed1.binance.org/",
            "https://bsc-dataseed2.binance.org/",
            "https://bsc-dataseed3.binance.org/",
            "https://bsc-dataseed4.binance.org/",
        ],
        "chain_type": ChainType.mainnet,
        "max_chunk_scan_size": 3000,
    },
    Environment.testnet: {
        "min_block_number": 11981429,
        "default_asset": AssetsKey.BNB,
        "provider": "https://data-seed-prebsc-2-s3.binance.org:8545/",
        "explorer_api": "api-testnet.bscscan.com",
        "explorer_key": os.environ.get("BSCSCAN_KEY"),
        "gas_price": 10,
        "explorer": "testnet.bscscan.com",
        "chain_id": 97,
        "private_key": os.environ.get("TESTNET_PK"),
        "address": os.environ.get("TESTNET_ADDRESS"),
        "backup_providers": [
            "https://data-seed-prebsc-1-s1.binance.org:8545/",
            "https://data-seed-prebsc-1-s2.binance.org:8545/",
            "https://data-seed-prebsc-2-s2.binance.org:8545/",
            "https://data-seed-prebsc-1-s3.binance.org:8545/",
        ],
        "chain_type": ChainType.testnet,
        "max_chunk_scan_size": 500000,
    },
    Environment.polygon_testnet: {
        "min_block_number": 23846272,
        "provider": "https://rpc-mumbai.maticvigil.com/",
        "default_asset": AssetsKey.MATIC,
        "gas_price": 2.5,
        "explorer_api": "api-mumbai.polygonscan.com",
        "explorer_key": os.environ.get("POLYGONSCAN_KEY"),
        "explorer": "mumbai.polygonscan.com",
        "chain_id": 80001,
        "private_key": os.environ.get("TESTNET_PK"),
        "address": os.environ.get("TESTNET_ADDRESS"),
        "backup_providers": [
            "https://rpc-mumbai.maticvigil.com/",
        ],
        "chain_type": ChainType.testnet,
        "max_chunk_scan_size": 100000,
    },
    Environment.polygon_mainnet: {
        "min_block_number": 5013591,
        "provider": "https://polygon-rpc.com/",
        "default_asset": AssetsKey.MATIC,
        "gas_price": 2.5,
        "explorer_api": "api.polygonscan.com",
        "explorer_key": os.environ.get("POLYGONSCAN_KEY"),
        "explorer": "polygonscan.com",
        "chain_id": 137,
        "private_key": os.environ.get("MAINNET_PK"),
        "address": os.environ.get("MAINNET_ADDRESS"),
        "backup_providers": [
            "https://rpc-mumbai.maticvigil.com/",
            "https://rpc-mainnet.matic.network",
            "https://matic-mainnet.chainstacklabs.com",
            "https://rpc-mainnet.maticvigil.com",
            "https://rpc-mainnet.matic.quiknode.pro",
            "https://matic-mainnet-full-rpc.bwarelabs.com"
        ],
        "chain_type": ChainType.mainnet,
        "max_chunk_scan_size": 10000,
    },
    Environment.avalanche_mainnet: {
        "min_block_number": 7388829,
        "default_asset": AssetsKey.AVAX,
        "provider": "https://api.avax.network/ext/bc/C/rpc",
        "explorer_api": "api.snowtrace.io",
        "explorer": "snowtrace.io",
        "explorer_key": os.environ.get("SNOWTRACE_KEY"),
        "chain_id": 43114,
        "private_key": os.environ.get("MAINNET_PK"),
        "address": os.environ.get("MAINNET_ADDRESS"),
        "backup_providers": [],
        "chain_type": ChainType.mainnet,
        "max_chunk_scan_size": 1000000,
    },
    Environment.fantom_testnet: {
        "min_block_number": 6997914,
        "provider": "https://rpc.testnet.fantom.network/",
        "default_asset": AssetsKey.FTM,
        "gas_price": 2.5,
        "explorer_api": "api-testnet.ftmscan.com",
        "explorer_key": os.environ.get("FMTSCAN_KEY"),
        "explorer": "testnet.ftmscan.com",
        "chain_id": 4002,
        "private_key": os.environ.get("TESTNET_PK"),
        "address": os.environ.get("TESTNET_ADDRESS"),
        "backup_providers": [],
        "chain_type": ChainType.testnet,
        "max_chunk_scan_size": 100000,
    },
    Environment.arbitrum_testnet: {
        "min_block_number": 9089497,
        "default_asset": AssetsKey.ETH,
        "provider": "https://rinkeby.arbitrum.io/rpc",
        "gas_price": 2.5,
        "explorer_api": "api-testnet.arbiscan.io",
        "explorer": "testnet.arbiscan.io",
        "explorer_key": os.environ.get("ARBISCAN_KEY"),
        "chain_id": 421611,
        "private_key": os.environ.get("TESTNET_PK"),
        "address": os.environ.get("TESTNET_ADDRESS"),
        "backup_providers": [],
        "chain_type": ChainType.testnet,
        "max_chunk_scan_size": 100000,
    },
    Environment.avalanche_testnet: {
        "min_block_number": 5052156,
        "default_asset": AssetsKey.AVAX,
        "provider": "https://api.avax-test.network/ext/bc/C/rpc",
        "explorer_api": "api-testnet.snowtrace.io",
        "explorer": "testnet.snowtrace.io",
        "explorer_key": os.environ.get("SNOWTRACE_KEY"),
        "chain_id": 43113,
        "private_key": os.environ.get("TESTNET_PK"),
        "address": os.environ.get("TESTNET_ADDRESS"),
        "backup_providers": [],
        "gas_price": 27.5,
        "chain_type": ChainType.testnet,
        "max_chunk_scan_size": 100000,
    },
    Environment.ropsten: {
        "min_block_number": 11909003,
        "default_asset": AssetsKey.ETH,
        "provider": "https://ropsten.infura.io/v3/409a281621734f66a517ec8a9ee0d12f",
        "explorer_api": "api-ropsten.etherscan.io",
        "explorer": "ropsten.etherscan.io/",
        "explorer_key": os.environ.get("ETHERSCAN_KEY"),
        "chain_id": 3,
        "private_key": os.environ.get("TESTNET_PK"),
        "address": os.environ.get("TESTNET_ADDRESS"),
        "backup_providers": [],
        "gas_price": 27.5,
        "chain_type": ChainType.testnet,
        "max_chunk_scan_size": 100000,
    },
    Environment.aurora_test: {
        "min_block_number": 81065420,
        "default_asset": AssetsKey.ETH,
        "provider": "https://testnet.aurora.dev/",
        "explorer_api": "explorer.testnet.aurora.dev",
        "explorer": "explorer.testnet.aurora.dev/",
        "explorer_key": "",
        "chain_id": 1313161555,
        "private_key": os.environ.get("TESTNET_PK"),
        "address": os.environ.get("TESTNET_ADDRESS"),
        "backup_providers": [],
        "gas_price": 0,
        "chain_type": ChainType.testnet,
        "max_chunk_scan_size": 100000,
    },
    Environment.aurora_mainnet: {
        "min_block_number": 81065420,
        "default_asset": AssetsKey.ETH,
        "provider": " https://mainnet.aurora.dev/13gvrutJ1W53h8tAmcjtY7xjDLGzSwZ5FnLKHYF9aone",
        "explorer_api": "explorer.mainnet.aurora.dev",
        "explorer": "explorer.mainnet.aurora.dev/",
        "explorer_key": "",
        "chain_id": 1313161554,
        "private_key": os.environ.get("MAINNET_PK"),
        "address": os.environ.get("MAINNET_ADDRESS"),
        "backup_providers": [],
        "gas_price": 0,
        "chain_type": ChainType.mainnet,
        "max_chunk_scan_size": 100000,
    },
}
