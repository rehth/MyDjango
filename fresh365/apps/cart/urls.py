from django.conf.urls import url
from apps.cart import views

urlpatterns = [
    # 添加购物车
    url(r'^add$', views.CartAdd.as_view(), name='add'),
    # 显示购物车页面
    url(r'^$', views.CartInfo.as_view(), name='info'),
    # 更新购物车数据/cart/update
    url(r'^update$', views.CartUpdate.as_view(), name='update'),
]