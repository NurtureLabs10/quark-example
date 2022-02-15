import json
from django.contrib.postgres.fields import JSONField


class JsonFieldTransitionHelper(JSONField):
    def from_db_value(self, value, expression, connection, context):
            if isinstance(value, str):
                return json.loads(value)
            return value
