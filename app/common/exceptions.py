from fastapi import status
from common.helpers import EXCEPTION_CODES
from .utils.error_wrapper import error_wrapper


class ErrorMessage(Exception):

    def __init__(self, msg):
        self.value = msg

    def __str__(self):
        return repr(self.value)

# class HttpResponseException(Exception):

#     def __init__(self, response="", meta="", status=403):
#         self.response = response
#         self.status = status
#         self.meta = meta
#         super(Exception, self).__init__(
#             meta + ". Status Code: " + str(status))

#     def __str__(self):
#         return ("Response: {response}, Meta: {meta}, Status: {status}".format(response=self.response, meta=self.meta, status=self.status))

class BaseException(Exception):

    def __dict__(self):
        return self.get_json()
    
    def __repr__(self):
        return self.get_json()
    
    def get_json(self):
        return {}


class InvalidSerializerInputException(BaseException):
    
    def __init__(self, errors):
        self.response = ', '.join(error_wrapper(errors))
        self.status = status.HTTP_400_BAD_REQUEST
        self.meta = 'InvalidInputException'
        super().__init__()

    def __str__(self):
        return ("Response: {response}, Meta: {meta}, Status: {status}".format(response=self.response, meta=self.meta, status=self.status))

    def get_json(self):
        return {
            "message": self.response,
            "type": self.meta,
            "code": self.status
        }


class NotAllowedException(BaseException):

    def __init__(self, response="", meta=None, status=status.HTTP_403_FORBIDDEN):
        self.response = response
        self.status = status
        self.meta = meta if meta else self.__class__.__name__
        super().__init__()

    def __str__(self):
        return ("Response: {response}, Meta: {meta}, Status: {status}".format(response=self.response, meta=self.meta, status=self.status))

    def get_json(self):
        return {
            "message": self.response,
            "type": self.meta,
            "code": self.status
        }

class NotExpectedException(BaseException):

    def __init__(self, response="", meta="", status=500):
        self.response = response
        self.status = status
        self.meta = meta
        super(Exception, self).__init__(
            meta + ". Status Code: " + str(status))

    def __str__(self):
        return ("Response: {response}, Meta: {meta}, Status: {status}".format(response=self.response, meta=self.meta, status=self.status))

    def get_json(self):
        return {
            "message": self.response,
            "type": self.meta,
            "code": self.status
        }

class NotFoundException(BaseException):

    def __init__(self, response="", meta=None, status=status.HTTP_404_NOT_FOUND):
        self.response = response
        self.status = status
        self.meta = meta if meta else self.__class__.__name__
        super().__init__()

    def __str__(self):
        return ("Response: {response}, Meta: {meta}, Status: {status}".format(response=self.response, meta=self.meta, status=self.status))

    def get_json(self):
        return {
            "message": self.response,
            "type": self.meta,
            "code": self.status
        }


class MultipleNotAcceptableError(BaseException):

    def __init__(self, responses=[], meta=None, status=status.HTTP_400_BAD_REQUEST):
        self.responses = responses
        self.status = status
        self.meta = meta if meta else self.__class__.__name__
        super().__init__()

    def __str__(self):
        return ("Response: {response}, Meta: {meta}, Status: {status}".format(response=str(self.responses), meta=self.meta, status=self.status))

    def get_json(self):
        return {
            "message": ', '.join(self.responses),
            "type": self.type,
            "code": self.status
        }


class NotAcceptableError(BaseException):

    def __init__(self, response, meta=None, status=status.HTTP_400_BAD_REQUEST):
        self.response = response
        self.status = status
        self.meta = meta if meta else self.__class__.__name__
        super().__init__()

    def __str__(self):
        return ("Response: {response}, Meta: {meta}, Status: {status}".format(response=self.response, meta=self.meta, status=self.status))

    def get_json(self):
        return {
            "message": self.response,
            "type": self.meta,
            "code": self.status
        }


# class AccountException(BaseException):

#     def __init__(self, types, meta="", message="", status=200):
#         self.message = message
#         self.types = types
#         self.meta = meta

#     def __str__(self):
#         error_msg = {
#             'meta': self.meta,
#             'data': {
#                 'error': {
#                     "message": self.message,
#                     "type": self.types,
#                     "code": EXCEPTION_CODES[self.types]
#                 }

#             }
#         }
#         return ("{}".format(error_msg))

#     def get_json(self):
#             return {
#             "message": self.message,
#             "type": self.type,
#             "code": self.status
#         }


class DBEntryError(BaseException):

    def __init__(self, response, meta=None, status=status.HTTP_500_INTERNAL_SERVER_ERROR):
        self.response = response
        self.status = status
        self.meta = meta if meta else self.__class__.__name__
        super().__init__()

    def __str__(self):
        return ("Response: {response}, Meta: {meta}, Status: {status}".format(response=self.response, meta=self.meta, status=self.status))

    def get_json(self):
        return {
            "message": self.response,
            "type": self.meta,
            "code": self.status
        }


class ResponseException(BaseException):

    def __init__(self, response, status, meta=None):
        self.response = response
        self.status = status
        self.meta = meta if meta else self.__class__.__name__
        super().__init__()

    def __str__(self):
        return ("Response: {response}, Meta: {meta}, Status: {status}".format(response=self.response, meta=self.meta, status=self.status))

    def get_json(self):
        return {
            "message": self.response,
            "type": self.meta,
            "code": self.status
        }

# class NotAcceptableError(ResponseException):

#     def __init__(self, param, param_value, response={}):
#         meta = '%s : %s Not Found' % (str(param), str(param_value))
#         super(NotAcceptableError, self).__init__(
#             meta, response, status.HTTP_406_NOT_ACCEPTABLE)


class ConflictError(ResponseException):

    def __init__(self, param, param_value, response={}):
        meta = '%s : %s Already Exists in Database' % (
            str(param), str(param_value))
        super(ConflictError, self).__init__(
            meta, response, status.HTTP_409_CONFLICT)
