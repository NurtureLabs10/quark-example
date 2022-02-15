from quark import Environment, ADDRESS_0

# Set the index app name here
INDEX_NAME = "index_v1"

MODELS = [
    "TokenBalance"
]

TOKEN_CONTRACT = {
    Environment.avalanche_mainnet: {
        "address": "0xB97EF9Ef8734C71904D8002F8b6Bc66Dd9c48a6E",
        "abi": "ERC20.json"
    },
    Environment.polygon_mainnet: {
        "address": '0x2791Bca1f2de4661ED88A30C99A7a9449Aa84174',
        "abi": "ERC20.json"
    }
}
