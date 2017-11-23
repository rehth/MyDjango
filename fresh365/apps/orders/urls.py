from django.conf.urls import url
from apps.orders import views


urlpatterns = [
    # 用户订单页面
    url(r'^$', views.OrderPlace.as_view(), name='place')
]
