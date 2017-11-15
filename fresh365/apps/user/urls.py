from django.conf.urls import url
from apps.user import views

urlpatterns = [
    url(r'^register$', views.Register.as_view(), name='register')
]
