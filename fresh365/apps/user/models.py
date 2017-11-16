from django.db import models
from db.base_model import BaseModel
from django.contrib.auth.models import AbstractUser
# Create your models here.


class User(AbstractUser, BaseModel):
    ''' 用户表的模型类 '''

    class Meta:
        db_table = 'user'
        verbose_name = '用户'
        verbose_name_plural = verbose_name


class AddressManager(models.Manager):
    """自定义地址模型类的管理器类"""
    # 1.过滤查询结果集
    # 2.封装函数
    def get_default_address(self, user):
        # self.model 可获取所属的模型类
        try:
            address = self.get(user=user, is_default=True)
        except self.model.DoesNotExist:
            address = None
        return address


class Address(BaseModel):
    '''　地址表的模型类　'''
    user = models.ForeignKey('User', verbose_name='所属用户')
    receiver = models.CharField(max_length=20, verbose_name='收件人')
    addr = models.CharField(max_length=256, verbose_name='收件地址')
    zip_code = models.CharField(max_length=6, verbose_name='邮政编码')
    phone = models.CharField(max_length=11, verbose_name='手机')
    is_default = models.BooleanField(default=False, verbose_name='是否默认')

    objects = AddressManager()

    class Meta:
        db_table = 'address'
        verbose_name = '地址'
        verbose_name_plural = verbose_name
