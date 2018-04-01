# -*- coding:utf-8 -*-
__author__ = 'ANdy'
from django.db import models

class BaseModel(models.Model):
    add_data=models.DateTimeField(auto_now_add=True)
    update_date=models.DateTimeField(auto_now_add=True)
    # 逻辑删除
    isDelete=models.BooleanField(default=False)

    class Meta:
        abstract=True

