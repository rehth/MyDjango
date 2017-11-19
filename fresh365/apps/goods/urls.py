from django.conf.urls import url
from apps.goods import views

urlpatterns = [
    url(r'^index$', views.Index.as_view(), name='index'),
    url(r'^goods', views.Detail.as_view(), name='detail'),
]
