# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('goods', '0002_auto_20171118_1657'),
    ]

    operations = [
        migrations.AlterField(
            model_name='goodssku',
            name='status',
            field=models.SmallIntegerField(default=1, verbose_name='状态', choices=[(1, '上架'), (2, '下架')]),
        ),
    ]
