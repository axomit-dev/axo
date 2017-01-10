from django.conf.urls import url
from . import views

# Namespacing
app_name = 'attendance'

urlpatterns = [
  url(r'^events/$', views.events, name='events'),
  url(r'^events/(?P<event_id>[0-9]+)/checkin/$', views.checkin, name='checkin'),
  url(r'^events/(?P<event_id>[0-9]+)/activate/$', views.activate, name='activate'),

]