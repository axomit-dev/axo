from django.conf.urls import url, include
from . import views

urlpatterns = [

  url(r'^$', views.index, name='index'),
  url(r'^credits/$', views.credits, name='credits'),
  url(r'^resources/$', views.resources, name='resources'),
]