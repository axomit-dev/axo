from django.conf.urls import url, include
from . import views

# Namespacing
app_name = 'house'

urlpatterns = [
  # Homepage
  url(r'^$', views.index, name='index'),

  url(r'^parking/$', views.parking, name='parking'),
  url(r'^dinner/$', views.dinner, name='dinner'),
]