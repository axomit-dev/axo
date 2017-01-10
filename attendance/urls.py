from django.conf.urls import url
from . import views

# Namespacing
app_name = 'attendance'

urlpatterns = [
  url(r'^events/$', views.events, name='events'),
]