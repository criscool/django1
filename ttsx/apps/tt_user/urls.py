# -*- coding:utf-8 -*-
__author__ = 'ANdy'
from django.conf.urls import url
from . import views
from django.contrib.auth.decorators import login_required

urlpatterns=[
    # url(r'^user$',views.user),
    url(r'^register$',views.RegisterView.as_view()),
    url(r'^active/(.+)$',views.active),
    url('^exists$', views.exists),
    url('^login$', views.LoginView.as_view()),
    url(r'^logout$',views.logout_user),
    url(r'^info$',views.info),
    url(r'^order$',views.order),
    # url(r'^site$',login_required(views.SiteView.as_view()))
    url(r'^site$',views.SiteView.as_view()),
    url(r'^area$',views.area)
]