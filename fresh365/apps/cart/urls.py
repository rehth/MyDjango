from django.conf.urls import url
from apps.cart import views

urlpatterns = [
    # 添加购物车
    url(r'^add$', views.CartAdd.as_view(), name='add'),
]