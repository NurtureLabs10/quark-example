def deep_get(x, path, default=None):
    attributes = path.split('__')
    return _deep_get(x, attributes, default)

def _deep_get(x, attributes, default=None):
    attribute = None
    try:
        attribute = attributes.pop(0)
    except IndexError:
        return x

    if not attribute:
        return x

    if attribute.isdigit():
        try:
            x = x[int(attribute)]
        except IndexError:
            return default
    else:
        try:
            x = x[attribute]
        except KeyError:
            return default
    return _deep_get(x, attributes, default)
