from fastapi.responses import JSONResponse


class MetaDataResponse(JSONResponse):
    meta_data_dict = {
        "meta": "",
        "data": {}
    }

    def __init__(self, *args, **kwargs):
        if kwargs.get('error'):
            error = kwargs.pop('error')
            MetaDataResponse.meta_data_dict["data"] = {"error": error}
            MetaDataResponse.meta_data_dict["meta"] = error.get('type')
        else:
            if args:
                MetaDataResponse.meta_data_dict["data"] = args[0]
                if len(args) >= 2:
                    MetaDataResponse.meta_data_dict["meta"] = args[1]
        modified_args = tuple([MetaDataResponse.meta_data_dict])
        super().__init__(*modified_args, **kwargs)
