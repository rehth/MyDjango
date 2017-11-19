from django.shortcuts import render
from django.views.generic import View
from apps.goods.models import GoodsType, IndexGoodsBanner, IndexPromotionBanner, IndexTypeGoodsBanner
from django_redis import get_redis_connection   # 创建与redis连接的类
from django.core.cache import cache
# Create your views here.


class Index(View):
    def get(self, request):
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


# /goods
class Detail(View):
    def get(self, request):
        return render(request, 'detail.html')
