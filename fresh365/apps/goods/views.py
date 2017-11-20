from django.shortcuts import render, redirect
from django.views.generic import View
from apps.goods.models import GoodsType, IndexGoodsBanner, \
    IndexPromotionBanner, IndexTypeGoodsBanner, GoodsSKU
from apps.orders.models import OrderGoods
from django_redis import get_redis_connection   # 创建与redis连接的类
from django.core.cache import cache
from django.core.urlresolvers import reverse
from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger
# Create your views here.


class Index(View):
    def get(self, request):
        # 获取cache.get(key) 返回value或None
        context = cache.get('index_info')
        # 如果对象不存在于缓存中，则cache.get()返回None
        if context is None:
            # print('设置了cache')   测试cache
            # 1.商品种类显示
            goods_types = GoodsType.objects.all()
            # 2.首页轮播商品展示
            banner = IndexGoodsBanner.objects.all().order_by('index')
            # 3.首页促销活动
            promotion = IndexPromotionBanner.objects.all().order_by('index')
            # 4.首页分类商品展示(图片/文字)
            for goods_type in goods_types:
                # 查询显示模式为标题的商品
                title = IndexTypeGoodsBanner.objects.filter(goods=goods_type, display_type=0)
                jpg = IndexTypeGoodsBanner.objects.filter(goods=goods_type, display_type=1)
                goods_type.title = title
                goods_type.banner = jpg
            # 构建上下文
            context = {'goods_types': goods_types, 'banner': banner,
                       'promotion': promotion}
            # 设置缓存cache.set(key, value, timeout)
            cache.set('index_info', context, 3600)
        # 获取购物车的中商品的数量  cart_user.id(hash) hlen
        user = request.user
        cart_content = 0
        if user.is_authenticated():
            conn = get_redis_connection('default')
            hash_key = 'cart_%d' % user.id
            cart_content = conn.hlen(hash_key)
        context.update(cart_content=cart_content)
        return render(request, 'index.html', context)


# /goods/sku_id
class Detail(View):
    def get(self, request, sku_id):
        # 1.商品信息
        try:
            sku = GoodsSKU.objects.get(id=sku_id, status=1)
        except GoodsSKU.DoesNotExist:
            return redirect(reverse('goods:index'))
        # 2.商品种类
        goods_types = GoodsType.objects.all()
        # 3.评论信息的订单30条
        sku_order = OrderGoods.objects.filter(sku=sku).order_by('-create_time')[0:30]
        # 4.新品推2个
        new_sku = GoodsSKU.objects.filter(goods=sku.goods, status=1).order_by('-create_time')[:2]
        # 5.获取购物车的中商品的数量 及添加浏览历史 cart_user.id(hash) hlen
        user = request.user
        cart_content = 0
        if user.is_authenticated():
            conn = get_redis_connection('default')
            hash_key = 'cart_%d' % user.id
            cart_content = conn.hlen(hash_key)
            # 浏览记录的添加  history_user.id [1,2,3]
            conn = get_redis_connection('default')
            history_key = 'history_%d' % user.id
            # 尝试移除列表中相同的sku_id  LREM key count value  count=0:移除表中所有与value相等的值
            conn.lrem(history_key, 0, sku_id)
            # 添加浏览记录
            conn.lpush(history_key, sku_id)
            # 对浏览记录进行修剪, 保留10条记录
            # LTRIM key start stop 列表修剪(trim)让列表只保留指定区间内的元素，不在指定区间之内的元素都将被删除
            conn.ltrim(history_key, 0, 9)

        # 6.构建上下文
        context = {'sku': sku, 'goods_types': goods_types,
                   'sku_comment': sku_order, 'new_sku': new_sku}
        context.update(cart_content=cart_content)
        return render(request, 'detail.html', context)


# list/(?P<kind>\d+)/(?P<pages>\d+)?sort='default/price/sales'
class GoodsList(View):
    def get(self, request, kind, pages):
        # 接受数据
        # 验证kind是否在goods_types范围内
        try:
            goods_kind = GoodsType.objects.get(id=kind)
        except GoodsType.DoesNotExist:
            goods_kind = GoodsType.objects.get(id=1)
        # 接受默认排序方式, 如果没有则返回default
        sort = request.GET.get('sort', 'default')
        if sort == 'price':
            # sku商品列表
            sku_list = GoodsSKU.objects.filter(goods=goods_kind, status=1).order_by('price')
        elif sort == 'hot':
            sku_list = GoodsSKU.objects.filter(goods=goods_kind, status=1).order_by('-sales')
        else:
            sort = 'default'
            sku_list = GoodsSKU.objects.filter(goods=goods_kind, status=1).order_by('-id')

        # 1.商品种类
        goods_types = GoodsType.objects.all()

        # 2.新品推荐
        new_sku = GoodsSKU.objects.filter(goods=goods_kind, status=1).order_by('-create_time')[:2]

        # 3.购物车的商品数量 cart_user.id  hash  当key不存在时，返回0
        user = request.user
        conn = get_redis_connection('default')
        cart_key = 'cart_%d' % user.id
        cart_content = conn.hlen(cart_key)

        # 分页操作
        paginator = Paginator(sku_list, 10)  # Show 10 contacts per page
        try:
            contacts = paginator.page(pages)
        except PageNotAnInteger:
            # If page is not an integer, deliver first page.
            contacts = paginator.page(1)
        except EmptyPage:
            # If page is out of range (e.g. 9999), deliver last page of results.
            contacts = paginator.page(paginator.num_pages)

        # 构建上下文
        context = {'goods_types': goods_types, 'cart_content': cart_content,
                   'goods_kind': goods_kind, 'page': contacts, 'new_sku': new_sku,
                   'sort': sort}
        return render(request, 'list.html', context)
