# -*- coding:utf-8 -*-
__author__ = 'ANdy'

from haystack import indexes
from .models import GoodsSKU

class GoodsSKUIndex(indexes.SearchIndex, indexes.Indexable):
    """建立索引时被使用的类 固定名字为text"""
    text = indexes.CharField(document=True, use_template=True)

    #针对哪张表进行查询
    def get_model(self):
        """从哪个表中查询"""
        return GoodsSKU
    #针对哪些行进行查询
    def index_queryset(self, using=None):
        """返回要建立索引的数据"""
        return self.get_model().objects.filter(isDelete=False)