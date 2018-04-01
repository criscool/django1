# coding=utf-8
from django.conf.urls import url
from . import views
urlpatterns=[
    url('^fdfs_test$',views.fdfs_test),
    url('^$',views.index),
    url('^(\d+)$',views.detail),
]