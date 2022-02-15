def error_wrapper(x):
    """
    x is will be a dictionary with the following structure
    {"error_type_1": [error1, error2], "error_type_1": [error1, error2] .....}
    return a list of the type
    ["error1", "error2", ...]
    """
    errors = list()
    for error_key, error_list in x.items():
        for error in error_list:
            if error_key == 'non_field_errors':
                errors.append(error)
            else:
                errors.append("%s: %s" % (error_key, error))
    return errors
