# -*- coding:utf-8 -*-
__author__ = 'ANdy'
from django.conf.urls import url
from . import views
urlpatterns=[
url(r'^add$',views.add)
]