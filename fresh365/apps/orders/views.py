from django.shortcuts import render, redirect
from django.views.generic import View
from utils.mixin import LoginRequiredMixin
from django.core.urlresolvers import reverse
from apps.user.models import Address
from apps.goods.models import GoodsSKU
from django_redis import get_redis_connection

# Create your views here.


# /order
class OrderPlace(LoginRequiredMixin):
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
            sku.amount = float('%.2f' % (int(sku.count)*float(sku.price)))
            total_price += sku.amount
            orders_sku.append(sku)

        # todo:业务处理
        # 运费
        trans_price = 10
        # 实际支付
        total_pay = total_price + trans_price
        # 收货地址
        addrs = Address.objects.filter(user=user)
        # todo:返回应答
        context = {
            'orders_sku': orders_sku, 'total_count': total_count,
            'trans_price': trans_price, 'total_pay': total_pay,
            'addrs': addrs, 'total_price': total_price
        }
        return render(request, 'test.html', context)
