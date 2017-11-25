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
from django.db import transaction
from django.conf import settings
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
        total_price = ('%.2f' % total_price)
        total_pay = ('%.2f' % (float(total_price) + trans_price))

        # 收货地址
        addrs = Address.objects.filter(user=user)
        # todo:返回应答
        sku_ids = ','.join(sku_ids)
        context = {
            'orders_sku': orders_sku, 'total_count': total_count,
            'trans_price': trans_price, 'total_pay': total_pay,
            'addrs': addrs, 'total_price': total_price, 'sku_ids': sku_ids
        }
        return render(request, 'place_order.html', context)


# ajax post请求 url:/orders/commit
# 参数：sku_ids, addr_id, pay_method
# mysql的事务实现
# 悲观锁测试
class OrdersCommit1(View):
    """订单提交"""
    def get(self, request):
        return redirect(reverse('cart:info'))

    @transaction.atomic
    def post(self, request):
        # todo:数据接受
        user = request.user
        sku_ids = request.POST.get('sku_ids')
        addr_id = request.POST.get('addr_id')
        pay_method = request.POST.get('pay_method')
        sku_ids = sku_ids.split(',')
        # todo:数据检验
        # 订单商品列表
        orders_sku = list()
        # 商品总数量
        total_count = 0
        # 商品总价格
        total_price = 0
        if not all([sku_ids, addr_id, pay_method]):
            return JsonResponse({'res': 0, 'msg': '信息不完整'})
        # pay_method
        for pay in OrderInfo.pay_method_choices:
            if int(pay_method) in pay:
                break
        else:
            return JsonResponse({'res': 1, 'msg': '支付方式有误'})
        # 收货地址
        try:
            addr = Address.objects.get(user=user, id=addr_id)
        except Address.DoesNotExist:
            return JsonResponse({'res': 2, 'msg': '收货地址有误'})

        # todo: 设置一个保存点
        sid = transaction.savepoint()

        # todo:业务处理-添加一个订单信息表, n个订单商品表
        # 订单信息表
        # 订单id:秒级时间戳+user.id
        try:
            order_id = datetime.datetime.now().strftime('%Y%m%d%H%M%S')+str(user.id)
            transit_price = 10
            orders = OrderInfo.objects.create(order_id=order_id, user=user,
                                              addr=addr, pay_method=pay_method,
                                              total_count=total_count, total_price=total_price,
                                              transit_price=transit_price, pay_id='Null')
            # 购物车查询
            conn = get_redis_connection('default')
            cart_key = 'cart_%s' % user.id
            # import time
            # time.sleep(10)
            for sku_id in sku_ids:
                try:
                    # 悲观锁测试  select_for_update()
                    sku = GoodsSKU.objects.select_for_update().get(id=sku_id)
                except GoodsSKU.DoesNotExist:
                    transaction.savepoint_rollback(sid)
                    return JsonResponse({'res': 3, 'msg': '商品不存在或已下架'})
                # 商品数量
                sku.count = conn.hget(cart_key, sku_id)    # b'4'
                # 商品库存检验
                if int(sku.count) > int(sku.stock):
                    transaction.savepoint_rollback(sid)
                    return JsonResponse({'res': 4, 'msg': '库存数量不足'})
                total_count += int(sku.count)
                # 商品小计
                amount = int(sku.count) * float(sku.price)
                sku.amount = float('%.2f' % amount)
                total_price += sku.amount
                orders_sku.append(sku)
            # 订单商品表
            for sku in orders_sku:
                OrderGoods.objects.create(order=orders, sku=sku,
                                          count=sku.count, price=sku.price,
                                          comment='Null')
                # 购物车数据更新
                conn.hdel(cart_key, sku.id)
                # order_info信息更新
                orders.total_count = total_count
                orders.total_price = total_price
                orders.save()
                # 商品库存更新
                sku.stock -= int(sku.count)
                # 商品销量
                sku.sales += int(sku.count)
                sku.save()
        except Exception as e:
            transaction.savepoint_rollback(sid)
            return JsonResponse({'res': 4, 'msg': e})
        # todo:事务提交
        transaction.savepoint_commit(sid)

        # todo:返回应答
        return JsonResponse(data={'res': 5, 'msg': '提交成功'})


# 乐观锁测试
class OrdersCommit(View):
    """订单提交"""
    def get(self, request):
        return redirect(reverse('cart:info'))

    @transaction.atomic
    def post(self, request):
        # todo:数据接受
        user = request.user
        sku_ids = request.POST.get('sku_ids')
        addr_id = request.POST.get('addr_id')
        pay_method = request.POST.get('pay_method')
        sku_ids = sku_ids.split(',')
        # todo:数据检验
        if not all([sku_ids, addr_id, pay_method]):
            return JsonResponse({'res': 0, 'msg': '信息不完整'})
        # pay_method
        for pay in OrderInfo.pay_method_choices:
            if int(pay_method) in pay:
                break
        else:
            return JsonResponse({'res': 1, 'msg': '支付方式有误'})
        # 收货地址
        try:
            addr = Address.objects.get(user=user, id=addr_id)
        except Address.DoesNotExist:
            return JsonResponse({'res': 2, 'msg': '收货地址有误'})
        # 商品总数量
        total_count = 0
        # 商品总价格
        total_price = 0
        # 购物车查询
        conn = get_redis_connection('default')
        cart_key = 'cart_%s' % user.id

        # todo: 设置一个保存点
        sid = transaction.savepoint()

        # todo:业务处理-添加一个订单信息表, n个订单商品表
        # 订单信息表
        # 订单id:秒级时间戳+user.id
        try:
            order_id = datetime.datetime.now().strftime('%Y%m%d%H%M%S')+str(user.id)
            transit_price = 10
            orders = OrderInfo.objects.create(order_id=order_id, user=user,
                                              addr=addr, pay_method=pay_method,
                                              total_count=total_count, total_price=total_price,
                                              transit_price=transit_price, pay_id='Null')
            for sku_id in sku_ids:
                for i in range(3):
                    try:
                        sku = GoodsSKU.objects.get(id=sku_id)
                    except GoodsSKU.DoesNotExist:
                        transaction.savepoint_rollback(sid)
                        return JsonResponse({'res': 3, 'msg': '商品不存在或已下架'})
                    # 商品数量
                    sku.count = conn.hget(cart_key, sku_id)  # b'4'
                    # 商品库存检验
                    if int(sku.count) > sku.stock:
                        transaction.savepoint_rollback(sid)
                        return JsonResponse({'res': 4, 'msg': '库存数量不足'})
                    # 更新前数据记录
                    original_stock = sku.stock
                    print('user:%s, stock:%s' % (user.username, original_stock))
                    new_stock = int(original_stock) - int(sku.count)
                    new_sales = int(sku.sales) + int(sku.count)

                    total_count += int(sku.count)
                    # 商品小计
                    amount = int(sku.count) * float(sku.price)
                    sku.amount = float('%.2f' % amount)
                    total_price += sku.amount

                    # 订单商品表
                    OrderGoods.objects.create(order=orders, sku=sku,
                                              count=sku.count, price=sku.price,
                                              comment='Null')
                    # 商品库存/商品销量更新
                    # 返回受影响的行数row
                    res = GoodsSKU.objects.filter(id=sku_id, stock=original_stock).\
                        update(stock=new_stock, sales=new_sales)
                    if not res:
                        # 更新失败
                        if i == 2:
                            # 订单添加失败，记录回滚
                            transaction.savepoint_rollback(sid)
                            return JsonResponse({'res': 7, 'msg': '订单提交失败'})
                        continue

                    # order_info信息更新
                    orders.total_count = total_count
                    orders.total_price = total_price
                    orders.save()
                    # 购物车数据更新
                    conn.hdel(cart_key, sku.id)
                    break

        except Exception as e:
            transaction.savepoint_rollback(sid)
            return JsonResponse({'res': 6, 'msg': e})
        # todo:事务提交
        transaction.savepoint_commit(sid)

        # todo:返回应答
        return JsonResponse(data={'res': 5, 'msg': '提交成功'})


# 订单支付 /orders/pay
# ajax post请求  params：order_id
class OrderPay(View):
    def post(self, request):
        # 登录验证
        user = request.user
        if not (user.is_authenticated() and user.is_active):
            return JsonResponse({'res': 0, 'msg': '请使用有效的用户身份登录'})
        # 获取数据user和order_id
        order_id = request.POST.get('order_id')
        # 数据校验
        if not order_id:
            return JsonResponse({'res': 1, 'msg': '数据不完整'})
        try:
            order = OrderInfo.objects.get(order_id=order_id, user=user, order_status=1)
        except OrderInfo.DoesNotExist:
            return JsonResponse({'res': 2, 'msg': '订单不存在或已付款'})

        # 业务处理
        # 调用支付宝接口，返回一个json数据，包括一个支付宝返回的url
        from alipay import AliPay
        import os
        # 使用支付宝python包的初始化
        alipay = AliPay(
            appid=settings.ALIPAY_APPID,
            app_notify_url=None,  # 默认回调url
            app_private_key_path=os.path.join(settings.BASE_DIR, 'apps/orders/app_private_key.pem'),
            alipay_public_key_path=os.path.join(settings.BASE_DIR, 'apps/orders/alipay_public_key.pem'),  # 支付宝的公钥
            sign_type="RSA2",  # RSA 或者 RSA2
            debug=True,  # 默认False表示实际支付环境 True表示开发环境
        )
        # 调用支付宝电脑pc端支付接口
        subject = "fresh365官方支付中心"
        pay = order.total_price + order.transit_price
        # 电脑网站支付，需要跳转到https://openapi.alipaydev.com/gateway.do? + order_string
        order_string = alipay.api_alipay_trade_page_pay(
            out_trade_no=str(order_id),   # 订单id
            total_amount=str(pay),         # 订单金额
            subject=subject,                # 订单标题
            return_url=None,
            notify_url=None  # 可选, 不填则使用默认notify url
        )
        # print(order_string)
        # 构建pay_url
        pay_url = 'https://openapi.alipaydev.com/gateway.do?' + order_string
        # 返回应答
        return JsonResponse({'res': 3, 'pay_url': pay_url})


# 查询用户订单是否支付成功
# 采用ajax post, 访问/order/check
class OrderCheck(View):
    def post(self, request):
        # 登录验证
        user = request.user
        if not (user.is_authenticated() and user.is_active):
            return JsonResponse({'res': 0, 'msg': '请使用有效的用户身份登录'})
        # 获取数据user和order_id
        order_id = request.POST.get('order_id')
        # 数据校验
        if not order_id:
            return JsonResponse({'res': 1, 'msg': '数据不完整'})
        try:
            order = OrderInfo.objects.get(order_id=order_id, user=user, order_status=1)
        except OrderInfo.DoesNotExist:
            return JsonResponse({'res': 2, 'msg': '订单不存在或已付款'})
        # 业务处理
        # 调用支付宝接口，返回一个json数据
        # alipay.trade.query(统一收单线下交易查询)
        from alipay import AliPay
        import os
        # 使用支付宝python包的初始化
        alipay = AliPay(
            appid=settings.ALIPAY_APPID,
            app_notify_url=None,  # 默认回调url
            app_private_key_path=os.path.join(settings.BASE_DIR, 'apps/orders/app_private_key.pem'),
            alipay_public_key_path=os.path.join(settings.BASE_DIR, 'apps/orders/alipay_public_key.pem'),  # 支付宝的公钥
            sign_type="RSA2",  # RSA 或者 RSA2
            debug=True,  # 默认False表示实际支付环境 True表示开发环境
        )
        # api_alipay_trade_query(self, out_trade_no=None, trade_no=None)
        while True:
            trade_res = alipay.api_alipay_trade_query(out_trade_no=order_id)
            """
            {
                "trade_no": "2017032121001004070200176844",
                "code": "10000",
                "invoice_amount": "20.00",
                "open_id": "20880072506750308812798160715407",
                "fund_bill_list": [
                  {
                    "amount": "20.00",
                    "fund_channel": "ALIPAYACCOUNT"
                  }
                ],
                "buyer_logon_id": "csq***@sandbox.com",
                "send_pay_date": "2017-03-21 13:29:17",
                "receipt_amount": "20.00",
                "out_trade_no": "out_trade_no15",
                "buyer_pay_amount": "20.00",
                "buyer_user_id": "2088102169481075",
                "msg": "Success",
                "point_amount": "0.00",
                "trade_status": "TRADE_SUCCESS",
                "total_amount": "20.00"
              }
            """
            code = trade_res.get('code')    # code（返回码）
            trade_status = trade_res.get('trade_status')   # trade_status
            print(code)
            # 详见https://docs.open.alipay.com/common/105806
            if code == '10000' and trade_status == 'TRADE_SUCCESS':
                # 用户支付成功 支付编号，订单状态更新
                pay_id = trade_res.get('trade_no')
                order.order_status = 4
                order.pay_id = pay_id
                order.save()
                return JsonResponse({'res': 3, 'msg': '支付成功'})
            elif code == '40004' or (code == '10000' and trade_status == 'WAIT_BUYER_PAY'):
                # 40004：业务处理失败 / 接口调用成功，等待用户支付
                import time
                time.sleep(3)
                continue
            else:
                return JsonResponse({'res': 4, 'msg': '支付失败'})
