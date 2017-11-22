from django.shortcuts import render
from django.http import JsonResponse
from django.views.generic import View
from utils.mixin import LoginRequiredMixin
from apps.goods.models import GoodsSKU
from django_redis import get_redis_connection

# Create your views here.


# ajax请求 post $.post(URL,data,callback);
# param: {count, sku_id, csrf}
# /card/add
class CartAdd(LoginRequiredMixin):
    def post(self, request):
        # todo:接收数据
        count = request.POST.get('count')
        sku_id = request.POST.get('sku_id')
        # todo:数据校验
        if not all([count, sku_id]):
            print(count + ':' + sku_id)
            return JsonResponse({'res': 1, 'msg': '数据不完整'})
        try:
            count = int(count)
        except Exception:
            return JsonResponse({'res': 2, 'msg': '商品数量发生错误'})
        try:
            sku = GoodsSKU.objects.get(id=sku_id, status=1)
        except GoodsSKU.DoesNotExist:
            return JsonResponse({'res': 3, 'msg': '商品不存在或已下架'})

        # todo:业务处理-添加购物车
        print('业务处理-添加购物车')
        user = request.user
        # 1.获取redis数据库连接
        conn = get_redis_connection('default')
        # 2.构建对应用户的购物车的名字
        cart_key = 'cart_%s' % user.id
        # 3.查询购物车中是否存在该商品
        sku_count = conn.hget(cart_key, sku_id)
        if sku_count:
            # 不同类型不能相加
            count += int(sku_count) + count

        # 数据校正-商品库存
        if count > int(sku.stock):
            return JsonResponse({'res': 4, 'msg': '超出商品库存'})
        # hset(name, key, value) 设置购物车数据
        conn.hset(cart_key, sku_id, count)

        # 4.查询购物车中商品sku类的数量
        kind = conn.hlen(cart_key)
        # todo:构建上下文
        context = {'res': 5, 'cart_count': kind, 'msg': '商品添加成功'}
        # todo:返回应答
        return JsonResponse(data=context)
