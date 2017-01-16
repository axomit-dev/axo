from django.conf.urls import url
from django.conf.urls import include
from . import views

# Namespacing
app_name = 'attendance'

urlpatterns = [
  url('^', include('django.contrib.auth.urls')),
  url(r'^$', views.index, name='index'),
  url(r'^sister/$', views.personal_record, name='personal_record'),
  url(r'^events/$', views.events, name='events'),
  url(r'^events/(?P<event_id>[0-9]+)/checkin/$', views.checkin, name='checkin'),
  url(r'^events/(?P<event_id>[0-9]+)/activate/$', views.activate, name='activate'),
  url(r'^events/(?P<event_id>[0-9]+)/checkin/sisters/(?P<sister_id>[0-9]+)$', views.checkin_sister, name='checkin_sister'),
]