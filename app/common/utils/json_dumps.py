import json
import datetime

 
def default(o):
    if isinstance(o, (datetime.date, datetime.datetime)):
        return o.isoformat()    
    try:
        return float(o)
    except:
        return str(o)


def json_dumps(o):
    return json.dumps(
        o,
        default=default
    )

def make_json_serializable(o):
    return json.loads(json_dumps(o))

