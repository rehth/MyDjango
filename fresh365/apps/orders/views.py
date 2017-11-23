from django.shortcuts import render, redirect
from django.views.generic import View
from utils.mixin import LoginRequiredMixin
from django.core.urlresolvers import reverse
from apps.user.models import Address
from apps.goods.models import GoodsSKU
from django_redis import get_redis_connection
from apps.orders.models import OrderInfo, OrderGoods
import datetime
from django.http import JsonResponse

# Create your views here.


# /order
class OrderPlace(LoginRequiredMixin):
    """订单页面显示"""
    def get(self, request):
        return redirect(reverse('cart:info'))

    def post(self, request):
        # todo:获取数据
        user = request.user
        sku_ids = request.POST.getlist('sku_ids')
        # print(sku_ids)  ['5', '3', '4']
        # todo:数据校验
        # 订单商品列表
        orders_sku = list()
        # 商品总数量
        total_count = 0
        # 商品总价格
        total_price = 0
        for sku_id in sku_ids:
            try:
                sku = GoodsSKU.objects.get(id=sku_id)
            except GoodsSKU.DoesNotExist:
                continue
            # 购物车查询
            conn = get_redis_connection('default')
            cart_key = 'cart_%s' % user.id
            # 商品数量
            sku.count = conn.hget(cart_key, sku_id)
            total_count += int(sku.count)
            # 商品小计
            amount = int(sku.count)*float(sku.price)
            sku.amount = float('%.2f' % amount)
            total_price += sku.amount
            orders_sku.append(sku)

        # todo:业务处理
        # 运费
        trans_price = 10
        # 实际支付
        total_price = float('%.2f' % total_price)
        total_pay = total_price + trans_price

        # 收货地址
        addrs = Address.objects.filter(user=user)
        # todo:返回应答
        # sku_ids = ','.join(sku_ids)
        context = {
            'orders_sku': orders_sku, 'total_count': total_count,
            'trans_price': trans_price, 'total_pay': total_pay,
            'addrs': addrs, 'total_price': total_price, 'sku_ids': sku_ids
        }
        return render(request, 'test.html', context)


# ajax post请求 url:/orders/commit
# 参数：sku_ids, addr_id, pay_method
class OrdersCommit(LoginRequiredMixin):
    """订单提交"""
    def get(self, request):
        return redirect(reverse('cart:info'))

    def post(self, request):
        # todo:数据接受
        user = request.user
        sku_ids = list(request.POST.get('sku_ids'))
        addr_id = request.POST.get('addr_id')
        pay_method = request.POST.get('pay_method')
        # todo:数据检验
        # 订单商品列表
        orders_sku = list()
        # 商品总数量
        total_count = 0
        # 商品总价格
        total_price = 0
        if not all([sku_ids, addr_id, pay_method]):
            return
        for sku_id in sku_ids:
            try:
                sku = GoodsSKU.objects.get(id=sku_id)
            except GoodsSKU.DoesNotExist:
                return
            # 购物车查询
            conn = get_redis_connection('default')
            cart_key = 'cart_%s' % user.id
            # 商品数量
            sku.count = conn.hget(cart_key, sku_id)
            # 商品库存检验
            if sku.count > sku.stock:
                return
            total_count += int(sku.count)
            # 商品小计
            amount = int(sku.count) * float(sku.price)
            sku.amount = float('%.2f' % amount)
            total_price += sku.amount
            orders_sku.append(sku)
        # pay_method
        for pay in OrderInfo.pay_method_choices.keys():
            if pay_method in pay:
                break
        else:
            return
        # 收货地址
        try:
            addr = Address.objects.get(user=user, id=addr_id)
        except Address.DoesNotExist:
            return
        # todo:业务处理-添加一个订单信息表, n个订单商品表
        # 订单信息表
        # 订单id:秒级时间戳+user.id
        order_id = datetime.datetime.now().strftime('%Y%m%d%H%M%S')+str(user.id)
        transit_price = 10
        orders = OrderInfo.objects.create(order_id=order_id, user=user,
                                          addr=addr, pay_method=pay_method,
                                          total_count=total_count, total_price=total_price,
                                          transit_price=transit_price, pay_id='Null')
        # 订单商品表
        for sku in orders_sku:
            OrderGoods.objects.create(order=orders, sku=sku,
                                      count=sku.count, price=sku.price,
                                      comment='Null')
            # 购物车数据更新
            # 商品库存更新

        # todo:返回应答
        return JsonResponse(data=None)


