from django.conf.urls import url
from apps.user import views

urlpatterns = [
    url(r'^$', views.UserCenter.as_view(), name='center'),
    url(r'^register$', views.Register.as_view(), name='register'),
    url(r'^active/(?P<val>.*)', views.Active.as_view(), name='active'),
    url(r'^login$', views.Login.as_view(), name='login'),
    url(r'^logout$', views.Logout.as_view(), name='logout'),
    url(r'^site$', views.UserSite.as_view(), name='site'),
    url(r'^order$', views.UserOrder.as_view(), name='order')
]
