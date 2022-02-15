from common import models
from quark.models import *
from .config import ADDRESS_0, INDEX_NAME


class TokenBalance(models.ActiveModel):
    contract = models.ForeignKey(Contract, on_delete=models.CASCADE)
    account = models.CharField(max_length=500)
    balance = models.DecimalField(max_digits=30, decimal_places=0, default=0)

    @classmethod
    def update_ledger(cls, contract, _from, _to, amount):
        _from_balance, _ = cls.objects.get_or_create(
            contract=contract,
            account=_from
        )
        _to_balance, _ = cls.objects.get_or_create(
            contract=contract,
            account=_to
        )

        if _from_balance != ADDRESS_0:
            _from_balance.balance -= amount
            _from_balance.save()
        if _to_balance != ADDRESS_0:
            _to_balance.balance += amount
            _to_balance.save()
    balance = models.DecimalField(max_digits=30, decimal_places=0, default=0)

    @classmethod
    def update_ledger(cls, contract, _from, _to, amount):
        _from_balance, _ = cls.objects.get_or_create(
            contract=contract,
            account=_from
        )
        _to_balance, _ = cls.objects.get_or_create(
            contract=contract,
            account=_to
        )

        if _from_balance != ADDRESS_0:
            _from_balance.balance -= amount
            _from_balance.save()
        if _to_balance != ADDRESS_0:
            _to_balance.balance += amount
            _to_balance.save()


class TransactionLog(models.Model):
    txn = models.ForeignKey(Txn, on_delete=models.CASCADE,
                            related_name=f"{INDEX_NAME}_txn")
    contract = models.ForeignKey(
        Contract, on_delete=models.CASCADE, related_name=f"{INDEX_NAME}_contract")
    data = models.JSONField(default=dict)
    event_name = models.ForeignKey(
        EventName, on_delete=models.CASCADE, related_name=f"{INDEX_NAME}_event_name")
    log_index = models.IntegerField()
    reference_key = models.CharField(max_length=500)

    class Meta:
        indexes = [
            models.Index(fields=['reference_key',]),
        ]
        unique_together = [
            ['txn', 'contract', 'log_index'],
        ]
