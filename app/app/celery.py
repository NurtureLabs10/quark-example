import os
import django
from celery import Celery
from django.conf import settings
from django.utils import timezone
import importlib

import logging

logger = logging.getLogger(__name__)


os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'app.settings')

django.setup()


class UTCCelery(Celery):
    """
    A Class to fix the Timezone issue for the Redis Broker.

    Saw this recommendation here.
    https://github.com/celery/celery/issues/4400
    """

    def now(self):
        """Return the current time and date as a datetime."""
        return timezone.now()


# patch(celery=True)
app = UTCCelery('app')
app.config_from_object('django.conf:settings', namespace='CELERY')
app.autodiscover_tasks()


@app.task(bind=True)
def debug_task(self):
    print('Request: {0!r}'.format(self.request))


@app.on_after_configure.connect
def setup_periodic_tasks(sender, **kwargs):
    if os.environ.get('ENVIRONMENT', 'local') == 'production':
        for app_name in settings.CUSTOM_APPS:
            try:
                tasks = importlib.import_module(f"{app_name}.tasks")
                for function_name in tasks.__dict__:
                    if function_name.startswith('periodic_'):
                        period_in_minutes = int(function_name.split('_')[1])
                        sender.add_periodic_task(
                            60 * period_in_minutes,
                            getattr(tasks, function_name).s()
                        )
            except (ModuleNotFoundError, AttributeError) as e:
                pass
            except Exception as e:
                logger.exception(e)


@app.task
def test(arg):
    print(arg)
