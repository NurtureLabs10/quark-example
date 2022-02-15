# from dotenv import load_dotenv
import os
from corsheaders.defaults import default_methods
from corsheaders.defaults import default_headers
from kombu import Queue
import sentry_sdk
from sentry_sdk.integrations.redis import RedisIntegration
from sentry_sdk.integrations.django import DjangoIntegration

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

# load_dotenv(os.path.join(BASE_DIR, 'env.env'))

SECRET_KEY = "secret-key"
DEBUG = False
ALLOWED_HOSTS = ['*']
DEFAULT_AUTO_FIELD = 'django.db.models.AutoField'

# Application definition
CUSTOM_APPS = [
    'common',
    'quark',
    'index_v1',
    'usdc_token'
]

THIRD_PARTY_APPS = [
    'django_celery_beat',
    'django_extensions',
    'bulk_update_or_create'
]

INSTALLED_APPS = [
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
    'corsheaders',
    *CUSTOM_APPS,
    *THIRD_PARTY_APPS
]

# MIDDLEWARE = [
#     'django.middleware.security.SecurityMiddleware',
#     'django.contrib.sessions.middleware.SessionMiddleware',
#     'corsheaders.middleware.CorsMiddleware',
#     'django.middleware.common.CommonMiddleware',
#     'django.middleware.csrf.CsrfViewMiddleware',
#     'django.contrib.auth.middleware.AuthenticationMiddleware',
#     'django.contrib.messages.middleware.MessageMiddleware',
#     'django.middleware.clickjacking.XFrameOptionsMiddleware'
#     # 'bugsnag.django.middleware.BugsnagMiddleware',
# ]

MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'corsheaders.middleware.CorsMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware'
    # 'bugsnag.django.middleware.BugsnagMiddleware',
]

# BUGSNAG = {
#     'api_key': os.environ.get('BUGSNAG_KEY'),
#     'project_root': BASE_DIR,
#     "notify_release_stages": ['development', 'production'],
#     "release_stage": os.environ.get('BUGSNAG_ENV', 'development'),
# }


LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'filters': {
        'require_debug_false': {
            '()': 'django.utils.log.RequireDebugFalse'
        }
    },
    'formatters': {
        'verbose': {
            'format': ('%(levelname)s %(asctime)s %(module)s'
                       ' %(process)d %(thread)d %(message)s'),
        },
        'simple': {
            'format': '%(levelname)s %(message)s',
        },
    },
    # 'root': {
    #     'level': 'INFO',
    #     'handlers': [
    #         'bugsnag',
    #         "console"
    #     ],
    # },
    'handlers': {
        'mail_admins': {
            'level': 'ERROR',
            'filters': ['require_debug_false'],
            'class': 'django.utils.log.AdminEmailHandler'
        },
        'console': {
            'level': 'INFO',
            'class': 'logging.StreamHandler',
            'formatter': 'simple',
        },
        'celery': {
            'level': 'INFO',
            'class': 'logging.handlers.RotatingFileHandler',
            'filename': 'celery.log',
            'formatter': 'simple',
            'maxBytes': 1024 * 1024 * 100,  # 100 mb
        }
        # 'bugsnag': {
        #     'level': 'WARNING',
        #     'class': 'bugsnag.handlers.BugsnagHandler',
        # }
    },
    'loggers': {
        'django_celery_beat': {
            'handlers': ['console'],
            'level': 'INFO',
            # 'propagate': True,
        },
        'django': {
            'handlers': ['console'],
            'level': 'INFO',
            # 'propagate': False,
        },
        'django.backends': {
            'handlers': ['console'],
            'level': 'INFO',
            # 'propagate': False,
        },
        'django.request': {
            'handlers': ['console'],
            'level': 'INFO'
        },
        'celery': {
            'handlers': ['console'],
            'level': 'INFO',
            # 'propagate': False,
        },
    }
}

for app_name in CUSTOM_APPS:
    LOGGING['loggers'][app_name] = {
        'handlers': ['console'],
        'level': 'INFO',
        # 'propagate': True,
    }

CORS_ORIGIN_ALLOW_ALL = True
CORS_ALLOW_METHODS = list(default_methods)
CORS_ALLOW_HEADERS = list(default_headers) + \
    ['session-token', 'user-id', 'session_token', 'user_id']


ROOT_URLCONF = "app.urls"

TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": [],
        "APP_DIRS": True,
        "OPTIONS": {
            "context_processors": [
                "django.template.context_processors.debug",
                "django.template.context_processors.request",
                "django.contrib.auth.context_processors.auth",
                "django.contrib.messages.context_processors.messages",
            ]
        },
    }
]

# DATABASES = {
#     "default": {
#         "ENGINE": "django.db.backends.sqlite3",
#         "NAME": os.path.join(BASE_DIR, "db.sqlite3"),
#     }
# }


DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.postgresql',
        'NAME': os.environ.get('POSTGRES_DB'),
        'USER': os.environ.get('POSTGRES_USER'),
        'PASSWORD': os.environ.get('POSTGRES_PASSWORD'),
        'HOST': os.environ.get('POSTGRES_HOST'),
        'PORT': '5432'
    }
}


AUTH_PASSWORD_VALIDATORS = [
    {
        "NAME": "django.contrib.auth.password_validation.UserAttributeSimilarityValidator"
    },
    {"NAME": "django.contrib.auth.password_validation.MinimumLengthValidator"},
    {"NAME": "django.contrib.auth.password_validation.CommonPasswordValidator"},
    {"NAME": "django.contrib.auth.password_validation.NumericPasswordValidator"},
]


STATICFILES_FINDERS = (
    "django.contrib.staticfiles.finders.FileSystemFinder",
    "django.contrib.staticfiles.finders.AppDirectoriesFinder",
)
STATIC_URL = "/static/"
STATIC_ROOT = os.path.join(BASE_DIR, "staticfiles")


PROJECT_NAME = os.environ.get('PROJECT_NAME')

os.environ["DJANGO_ALLOW_ASYNC_UNSAFE"] = "true"


MASTER_SESSION_TOKEN = os.environ.get('MASTER_SESSION_TOKEN')
LOCAL_MODE = True

AWS_ACCESS_KEY_ID = os.environ.get('AWS_ACCESS_KEY_ID')
AWS_SECRET_ACCESS_KEY = os.environ.get('AWS_SECRET_ACCESS_KEY')
AWS_REGION = os.environ.get('AWS_REGION')

CELERY_BROKER_URL = 'redis://redis:6379'
# CELERY_BROKER_URL = 'redis://127.0.0.1:6379'

CELERY_BROKER_TRANSPORT = 'redis'
CELERY_BROKER_TRANSPORT_OPTIONS = {'visibility_timeout': 604800}

# CELERY_BROKER_TRANSPORT = 'sqs'
# CELERY_BROKER_TRANSPORT_OPTIONS = {
#     'region': 'ap-south-1',
# }
# CELERY_BROKER_USER = os.environ.get('AWS_ACCESS_KEY_ID')
# CELERY_BROKER_PASSWORD = os.environ.get('AWS_SECRET_ACCESS_KEY')

# TODO: make this generic
CELERY_IMPORTS = ('quark.tasks',)

CELERY_TASK_SERIALIZER = 'json'
CELERY_RESULT_SERIALIZER = 'json'

CELERY_RESULT_BACKEND = 'redis://redis:6379'

CELERY_ACCEPT_CONTENT = ['json']
CELERY_SEND_EVENTS = True
CELERY_SEND_TASK_SENT_EVENT = True
CELERY_ENVIRONMENT = os.environ.get('CELERY_ENV', 'prod')
DEFAULT_QUEUE_NAME = "default-{env}".format(env=CELERY_ENVIRONMENT)
# PRIORITY_QUEUE_NAME = "priority_high-{env}".format(env=CELERY_ENVIRONMENT)
# SCRAPING_QUEUE_NAME = "scraper-{env}".format(env=CELERY_ENVIRONMENT)
CELERY_TASK_DEFAULT_QUEUE = DEFAULT_QUEUE_NAME
CELERY_QUEUES = (Queue(DEFAULT_QUEUE_NAME),)

CELERYBEAT_SCHEDULER = "django_celery_beat.schedulers:DatabaseScheduler"
CELERYD_PREFETCH_MULTIPLIER = 1

BROKER_TRANSPORT_OPTIONS = {
    'visibility_timeout': 3600 * 5  # 5 hours
}

DJANGO_CELERY_BEAT_TZ_AWARE = True

CELERY_ALWAYS_EAGER = False
# CELERY_ALWAYS_EAGER = False

USE_TZ = True
TIME_ZONE = 'UTC'
CELERY_ENABLE_UTC = False
CELERY_TIMEZONE = TIME_ZONE

if os.environ.get('ENVIRONMENT', 'local') == 'production':
    sentry_sdk.init(
        dsn=os.environ.get('SENTRY_KEY'),
        integrations=[DjangoIntegration(), RedisIntegration()],
        traces_sample_rate=0.2,
        # If you wish to associate users to errors (assuming you are using
        # django.contrib.auth) you may enable sending PII data.
        send_default_pii=True
    )


NOTEBOOK_ARGUMENTS = [
    '--ip', '0.0.0.0',
    '--port', '8888',
    '--allow-root',
    '--no-browser',
]

PINATA_KEY = os.environ.get('PINATA_KEY')
PINATA_SECRET_KEY = os.environ.get('PINATA_SECRET_KEY')
