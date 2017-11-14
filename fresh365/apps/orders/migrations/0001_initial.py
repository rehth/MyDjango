# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
    ]

    operations = [
        migrations.CreateModel(
            name='OrderGoods',
            fields=[
                ('id', models.AutoField(serialize=False, primary_key=True, auto_created=True, verbose_name='ID')),
                ('create_time', models.DateField(auto_now_add=True, verbose_name='创建时间')),
                ('update_time', models.DateField(auto_now=True, verbose_name='更新时间')),
                ('is_delete', models.BooleanField(default=False, verbose_name='删除标记')),
                ('count', models.IntegerField(default=1, verbose_name='商品数目')),
                ('price', models.DecimalField(max_digits=10, verbose_name='商品价格', decimal_places=2)),
                ('comment', models.CharField(max_length=256, verbose_name='评论')),
            ],
            options={
                'db_table': 'order_goods',
                'verbose_name': '订单商品',
                'verbose_name_plural': '订单商品',
            },
        ),
        migrations.CreateModel(
            name='OrderInfo',
            fields=[
                ('create_time', models.DateField(auto_now_add=True, verbose_name='创建时间')),
                ('update_time', models.DateField(auto_now=True, verbose_name='更新时间')),
                ('is_delete', models.BooleanField(default=False, verbose_name='删除标记')),
                ('order_id', models.CharField(serialize=False, primary_key=True, max_length=128, verbose_name='订单id')),
                ('pay_method', models.SmallIntegerField(choices=[(1, '货到付款'), (2, '微信支付'), (3, '支付宝'), (4, '银联支付')], default=3, verbose_name='付款方式')),
                ('total_price', models.DecimalField(max_digits=10, verbose_name='总价', decimal_places=2)),
                ('total_count', models.IntegerField(default=1, verbose_name='数量')),
                ('transit_price', models.DecimalField(max_digits=10, verbose_name='运费', decimal_places=2)),
                ('order_status', models.SmallIntegerField(choices=[(1, '未支付'), (2, '待发货'), (3, '待收货'), (4, '待评价'), (5, '已完成')], default=1, verbose_name='订单状态')),
                ('pay_id', models.CharField(max_length=128, verbose_name='支付编号')),
            ],
            options={
                'db_table': 'order_info',
                'verbose_name': '订单信息',
                'verbose_name_plural': '订单信息',
            },
        ),
    ]
