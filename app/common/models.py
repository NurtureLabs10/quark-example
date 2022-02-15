from django.db.models import *
#from model_utils.models import TimeStampedModel
from django.forms.models import model_to_dict
from common.utils.json_dumps import json_dumps
from django.utils import timezone
import datetime

class ActiveObjectManager(Manager):
    # TODO: Check for is_active is all the related items too
    def get_queryset(self):
        return super(ActiveObjectManager, self)\
            .get_queryset()\
            .filter(is_active=True).order_by('pk')

def is_builtins(d):
    return d.__class__.__module__ == 'builtins'


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
    elif not is_builtins(d):
        d = d.json()
    return d

class ActiveModel(Model):
    created_at = DateTimeField(auto_now_add=True)
    updated_at = DateTimeField(auto_now=True)
    is_active = BooleanField(default=True)

    objects = Manager()
    active_objects = ActiveObjectManager()

    class Meta:
        abstract = True

    def __unicode__(self):
        return json_dumps(model_to_dict(self))

    def __str__(self):
        return json_dumps(model_to_dict(self))

    def json(self):
        return parse(model_to_dict(self))

    def deactivate(self):
        self.is_active = False
        # self.deleted_at = timezone.now()
        self.save()


class LifeTimeTrackingModel(ActiveModel):
    deleted_at = DateTimeField(null=True, blank=True)

    class Meta:
        abstract = True
    
    def deactivate(self):
        self.is_active = False
        self.deleted_at = timezone.now()
        self.save()


class InActiveModel(Model):
    created_at = DateTimeField(auto_now_add=True)
    updated_at = DateTimeField(auto_now=True)
    is_active = BooleanField(default=False)

    objects = Manager()
    active_objects = ActiveObjectManager()

    class Meta:
        abstract = True


class LimitLog(ActiveModel):
    ip_address = CharField(max_length=255,null=True, blank=True)
    user_address = CharField(max_length=255,null=True, blank=True)
    endpoint= CharField(max_length=255)
