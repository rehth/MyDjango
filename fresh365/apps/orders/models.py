from django.db import models
from db.base_model import BaseModel
# Create your models here.


class OrderInfo(BaseModel):
    ''' 订单信息模型类 '''
    pay_method_choices = (
        (1, '货到付款'),
        (2, '微信支付'),
        (3, '支付宝'),
        (4, '银联支付'),
    )
    order_status_choices = (
        (1, '未支付'),
        (2, '待发货'),
        (3, '待收货'),
        (4, '待评价'),
        (5, '已完成'),
    )
    order_id = models.CharField(max_length=128, primary_key=True, verbose_name='订单id')
    user = models.ForeignKey('user.User', verbose_name='用户')
    addr = models.ForeignKey('user.Address', verbose_name='地址')
    pay_method = models.SmallIntegerField(default=3, choices=pay_method_choices, verbose_name='付款方式')
    total_price = models.DecimalField(max_digits=10, decimal_places=2, verbose_name='总价')
    total_count = models.IntegerField(default=1, verbose_name='数量')
    transit_price = models.DecimalField(max_digits=10, decimal_places=2, verbose_name='运费')
    order_status = models.SmallIntegerField(default=1, verbose_name='订单状态', choices=order_status_choices)
    pay_id = models.CharField(max_length=128, verbose_name='支付编号')

    class Meta:
        db_table = 'order_info'
        verbose_name = '订单信息'
        verbose_name_plural = verbose_name


class OrderGoods(BaseModel):
    ''' 订单商品模型类 '''
    order = models.ForeignKey('OrderInfo', verbose_name='订单')
    count = models.IntegerField(default=1, verbose_name='商品数目')
    price = models.DecimalField(max_digits=10, decimal_places=2, verbose_name='商品价格')
    comment = models.CharField(max_length=256, verbose_name='评论')
    sku = models.ForeignKey('goods.GoodsSKU', verbose_name='商品sku')

    class Meta:
        db_table = 'order_goods'
        verbose_name = '订单商品'
        verbose_name_plural = verbose_name
