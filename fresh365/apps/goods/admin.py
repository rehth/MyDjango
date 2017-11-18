from django.contrib import admin
from apps.goods.models import GoodsType
# Register your models here.


@admin.register(GoodsType)
class GoodsType(admin.ModelAdmin):
    list_display = ['id', 'name', 'logo']