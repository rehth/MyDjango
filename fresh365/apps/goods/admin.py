from django.contrib import admin
from apps.goods.models import GoodsType, IndexPromotionBanner
# Register your models here.


class BaseModelAdmin(admin.ModelAdmin):
    """数据表中的数据发生改变时调用 生产新的静态页面index.html"""
    def save_model(self, request, obj, form, change):
        """新增或修改数据表中的数据时调用"""
        super().save_model(request, obj, form, change)
        from celery_tasks.tasks import generate_static_index_html
        # 生成静态页面index.html
        generate_static_index_html.delay()

    def delete_model(self, request, obj):
        """删除数据表中的数据时调用"""
        super().delete_model(request, obj)
        # 生成静态页面index.html
        from celery_tasks.tasks import generate_static_index_html
        generate_static_index_html.delay()


@admin.register(GoodsType)
class GoodsTypeAdmin(BaseModelAdmin):
    list_display = ['id', 'name', 'logo']


@admin.register(IndexPromotionBanner)
class IndexPromotionBannerAdmin(BaseModelAdmin):
    list_display = ['id', 'name', 'url']
