from common import models

# Logs
class Environment(models.Model):
    environment = models.CharField(max_length=255)

    class Meta:
        indexes = [
            models.Index(fields=['environment', ]),
        ]


class Block(models.Model):
    timestamp = models.DateTimeField()
    block_number = models.IntegerField()
    environment = models.ForeignKey(Environment, on_delete=models.CASCADE)

    class Meta:
        indexes = [
            # models.Index(fields=['environment',]),
            models.Index(fields=['block_number', ]),
        ]
        unique_together = [['environment', 'block_number']]


class Txn(models.Model):
    block = models.ForeignKey(Block, on_delete=models.CASCADE)
    hash = models.CharField(max_length=255)
    index = models.IntegerField()

    class Meta:
        indexes = [
            models.Index(fields=['hash', ]),
        ]
        unique_together = [['hash', 'block'], ['index', 'block']]


class Contract(models.Model):
    address = models.CharField(max_length=255)
    environment = models.ForeignKey(Environment, on_delete=models.CASCADE)

    class Meta:
        indexes = [
            models.Index(fields=['address', ]),
        ]
        unique_together = [['address']]


class EventName(models.Model):
    event_name = models.CharField(max_length=255)

    class Meta:
        indexes = [
            models.Index(fields=['event_name', ]),
        ]
        unique_together = [['event_name']]
