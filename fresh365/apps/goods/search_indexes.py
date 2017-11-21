from haystack import indexes
# 导入对应的模型类
from apps.goods.models import GoodsSKU


class GoodsSKUIndex(indexes.SearchIndex, indexes.Indexable):
    """指定某个类的某些数据建立索引 类名：模型类+Index"""
    # 使用数据模板（而不是容易出错的连接）来构建搜索引擎将索引的文档
    text = indexes.CharField(document=True, use_template=True)

    def get_model(self):
        """返回你的模型类"""
        return GoodsSKU

    def index_queryset(self, using=None):
        """建立索引的数据"""
        return self.get_model().objects.filter(status=1)