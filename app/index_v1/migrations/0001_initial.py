# Generated by Django 3.2.12 on 2022-02-15 01:25

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        ('quark', '0001_initial'),
    ]

    operations = [
        migrations.CreateModel(
            name='TransactionLog',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('data', models.JSONField(default=dict)),
                ('log_index', models.IntegerField()),
                ('reference_key', models.CharField(max_length=500)),
                ('contract', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='index_v1_contract', to='quark.contract')),
                ('event_name', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='index_v1_event_name', to='quark.eventname')),
                ('txn', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='index_v1_txn', to='quark.txn')),
            ],
        ),
        migrations.CreateModel(
            name='TokenBalance',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('is_active', models.BooleanField(default=True)),
                ('account', models.CharField(max_length=500)),
                ('balance', models.DecimalField(decimal_places=0, default=0, max_digits=30)),
                ('contract', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='quark.contract')),
            ],
            options={
                'abstract': False,
            },
        ),
        migrations.AddIndex(
            model_name='transactionlog',
            index=models.Index(fields=['reference_key'], name='index_v1_tr_referen_889a9f_idx'),
        ),
        migrations.AlterUniqueTogether(
            name='transactionlog',
            unique_together={('txn', 'contract', 'log_index')},
        ),
    ]
