from hexbytes import HexBytes
from web3.datastructures import AttributeDict

def parse(d):
    if not d:
        return d

    if isinstance(d, list):
        for i, k in enumerate(d):
            d[i] = parse(k)
    elif isinstance(d, dict) or isinstance(d, AttributeDict):
        d = dict(d)
        for k in d:
            d[k] = parse(d[k])
    elif isinstance(d, HexBytes):
        return d.hex()
    elif isinstance(d, bytes):
        return d.hex()
    return d
