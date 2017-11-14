from django.db import models
from db.base_model import BaseModel
from django.contrib.auth.models import AbstractUser
# Create your models here.


class User(AbstractUser, BaseModel):
    ''' 用户表的模型类 '''

    class Meta:
        db_table = 'fresh_user'
        verbose_name = '用户'
        verbose_name_plural = verbose_name

