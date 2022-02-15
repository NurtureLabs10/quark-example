from functools import wraps
from django.db import IntegrityError
from django.http import Http404
from django.conf import settings
import datetime
from fastapi.exceptions import RequestValidationError
from django.utils import timezone
from .responses import MetaDataResponse
from .exceptions import (
    NotAcceptableError,
    NotAllowedException,
    NotFoundException,
    MultipleNotAcceptableError,
)
from django.db import connections
from .limiter import RateLimitExceeded
from datetime import timedelta
from common.models import LimitLog
from django.db.models import Q
from .config import LIMITTER_COUNT
import logging

logger = logging.getLogger(__name__)


def session_authorize(user_id_key="pk", *args, **kwargs):
    def deco(f):
        def abstract_user_id(request, **kwargs):
            user_id = None
            if user_id_key in kwargs:
                user_id = kwargs[user_id_key]
            elif request.method == "GET":
                try:
                    user_id = request.query_params.get(user_id_key)[0]
                except TypeError:
                    user_id = None
            else:
                user_id = request.data.get(user_id_key)
            return int(user_id) if user_id else None

        def abstract_session_token(request, **kwargs):
            session_token_header_key = "HTTP_SESSION_TOKEN"
            session_token = request.META.get(session_token_header_key)
            if session_token:
                return session_token

            session_token_key = "session_token"
            if session_token_key in kwargs:
                session_token = kwargs[session_token_key]
            else:
                try:
                    session_token = request.query_params.get(session_token_key)
                except TypeError:
                    session_token = None

            return session_token

        @wraps(f)
        def decorated_function(*args, **kwargs):
            request = args[1]

            # For Admin APIs
            if user_id_key == "admin":
                auth_data = {
                    "user_id": user_id_key,
                    "session_token": abstract_session_token(request),
                }
                if auth_data["session_token"] in [
                    settings.ADMIN_TOKEN,
                    settings.MASTER_SESSION_TOKEN,
                ]:
                    auth_data["authorized"] = True
                    return f(auth_data=auth_data, *args, **kwargs)

            auth_data = {
                "user_id": abstract_user_id(request, **kwargs),
                "session_token": abstract_session_token(request),
            }

            (
                auth_data["authorized"],
                auth_data["user_id"],
            ) = authentication_service.Authentication(auth_data).validated_data()

            if not auth_data["authorized"]:
                # return unauthorised status
                return Response({}, status.HTTP_401_UNAUTHORIZED)

            return f(auth_data=auth_data, *args, **kwargs)

        return decorated_function

    return deco


def default_logger():
    logger = logging.getLogger("From the Decorator file")
    return logger


# def format_error(*args):
#     return {
#         "error": list(args)
#     }


def catch_exception(logger=default_logger()):
    def deco(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            try:
                return f(*args, **kwargs)

            except IntegrityError as e:
                logger.exception("IntegrityError:%s" % str(e))
                return MetaDataResponse(
                    error={"type": "IntegrityError", "message": str(e), "code": 400}
                )

            except Http404 as e:
                logger.exception(str(e))
                return MetaDataResponse(
                    error={
                        "type": "ObjectNotFoundError",
                        "message": str(e),
                        "code": 400,
                    }
                )

            except AssertionError as e:
                logger.exception(str(e))
                return MetaDataResponse(
                    error={"type": "AssertionError", "message": str(e), "code": 400}
                )

            except RequestValidationError as e:
                logger.exception(str(e))
                return MetaDataResponse(
                    error={
                        "type": "RequestValidationError",
                        "message": str(e),
                        "code": 400,
                    }
                )

            except RateLimitExceeded as e:
                logger.exception(str(e))
                return MetaDataResponse(
                    error={
                        "type": "RateLimitExceeded",
                        "message": f"Rate Limit Exceeded: Allowed rate limit is {e.detail}",
                        "code": 400,
                    }
                )

            except Exception as e:
                if hasattr(e, "get_json"):
                    logger.exception(f"Encountered Exception {e.get_json()}")
                    return MetaDataResponse(error=e.get_json())
                logger.exception(str(e))
                return MetaDataResponse(
                    error={
                        "type": "InternalServerException",
                        "message": str(e),
                        "code": 500,
                    },
                    status_code=500,
                )

        return decorated_function

    return deco


def parse(d):
    if not d:
        return d

    if isinstance(d, list):
        for i, k in enumerate(d):
            d[i] = parse(k)
    elif isinstance(d, dict):
        for k in d:
            d[k] = parse(d[k])
    elif isinstance(d, datetime.datetime):
        return d.isoformat()
    return d


def meta_data_response(meta=""):
    def deco(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            vanilla_response = parse(f(*args, **kwargs))
            # print(vanilla_response)
            return MetaDataResponse(vanilla_response, meta, status_code=200)

        return decorated_function

    return deco


def close_db_connection():
    def deco(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            response = f(*args, **kwargs)
            connections["default"].close()
            return response

        return decorated_function

    return deco


def api_wrapper(f):
    return catch_exception()(meta_data_response()(close_db_connection()(f)))


def limiter(*args, **kwargs):
    def deco(f):
        @wraps(f)
        def decorated_function(request, *args, **kwargs):
            user_address = request.query_params["user_address"]
            is_existing_user = Q(ip_address=request.client.host) | Q(
                user_address=user_address
            )
            log_count = LimitLog.active_objects.filter(
                is_existing_user,
                created_at__gte=timezone.now() - timedelta(days=1),
                endpoint=request.url.path,
            ).count()
            if log_count < LIMITTER_COUNT:
                response = f(*args, **kwargs)
                LimitLog.objects.create(
                    ip_address=request.client.host,
                    endpoint=request.url.path,
                    user_address=user_address,
                )
                return response
            else:
                raise NotAcceptableError("Maximum Limit for API reached")

        return decorated_function

    return deco


def cached_property(f):
    @wraps(f)
    def decorated_function(instance, *args, **kwargs):
        var_name = f"_var_{f.__name__}"
        if hasattr(instance, var_name):
            return getattr(instance, var_name)
        var_value = f(instance, *args, **kwargs)
        setattr(instance, var_name, var_value)
        return var_value

    x = property(fget=decorated_function)

    return x
