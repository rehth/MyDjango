from django.conf.urls import url
from apps.goods import views

urlpatterns = [
    url(r'^index$', views.Index.as_view(), name='index'),
    url(r'^goods/(?P<sku_id>\d+)', views.Detail.as_view(), name='detail'),
    url(r'^list/(?P<kind>\d+)/(?P<pages>\d+)', views.GoodsList.as_view(), name='list')
]
