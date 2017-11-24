from django.conf.urls import url
from apps.orders import views


urlpatterns = [
    # 用户订单页面
    url(r'^$', views.OrderPlace.as_view(), name='place'),
    # 用户订单提交 /orders/commit
    url(r'^commit$', views.OrdersCommit.as_view(), name='commit')

]
