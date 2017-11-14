from django.db import models


class BaseModel(models.Model):
    '''　模型类的抽象基类　'''
    # auto_now_add=True 记录第一次创建的时间 实例第一次保存的时候会保存当前时间
    create_time = models.DateField(auto_now_add=True, verbose_name='创建时间')
    # auto_now=True，字段保存时会自动保存当前时间,实例执行save()的时候都会将当前时间保存
    update_time = models.DateField(auto_now=True, verbose_name='更新时间')
    # BooleanField 布尔字段　默认为False
    is_delete = models.BooleanField(default=False, verbose_name='删除标记')

    class Meta:
        # 说明是一个抽象模型类
        # 不可以实例化, 即不可以用new创建对象 抽象类中可以没有抽象方法,可以有实体方法
        # 决定子类中必须实现的方法和特性
        abstract = True
