# from dotenv import load_dotenv
import os
# load_dotenv()

from django.apps import apps
from django.conf import settings
from django.core.wsgi import get_wsgi_application
from fastapi import FastAPI
from starlette.middleware.cors import CORSMiddleware
import importlib
from django.core.wsgi import get_wsgi_application
import sentry_sdk
from sentry_sdk.integrations.asgi import SentryAsgiMiddleware
from sentry_sdk.integrations.celery import CeleryIntegration
from sentry_sdk.integrations.django import DjangoIntegration
from starlette.staticfiles import StaticFiles

from common.limiter import limiter
import logging
logger = logging.getLogger(__name__)


sentry_sdk.init(
    dsn=os.environ.get('SENTRY_DSN'),
    traces_sample_rate=0.2,
    integrations=[DjangoIntegration(), CeleryIntegration()]
)


os.environ.setdefault("DJANGO_SETTINGS_MODULE", "app.settings")

application = get_wsgi_application()


def get_application() -> FastAPI:
    app = FastAPI(
        title=os.environ.get('PROJECT_NAME'),
        description="The public APIs for the Quark Example Web App"
    )
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.ALLOWED_HOSTS or ["*"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )
    for app_name in settings.CUSTOM_APPS:
        app_module = importlib.import_module(app_name)
        try:
            app.include_router(
                importlib.import_module(f"{app_name}.endpoints").api_router,
                prefix=""
            )
        except ModuleNotFoundError:
            pass

    app.mount("/static", StaticFiles(directory="staticfiles"))

    return app


app = get_application()
app.state.limiter = limiter

if os.environ.get('ENVIRONMENT', 'local') == 'production':
    app = SentryAsgiMiddleware(app)

# Register all contracts

# for app_name in settings.CUSTOM_APPS:
#     if app_name not in ["quark", "common"]:
#         logger.info("*"*10 + f"Registering Contracts in {app_name}" + "*"*10)
#         try:
#             importlib.import_module(f"{app_name}.track_contract").register()
#         except (ModuleNotFoundError, AttributeError) as e:
#             # logger.warning(f"{app_name}: No contracts to track")
#             pass
#         except Exception as e:
#             logger.exception(e)
