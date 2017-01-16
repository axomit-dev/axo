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

  url(r'^excuses/write/(?P<event_id>[0-9]+)/$', views.excuse_write, name='excuse_write'),
  url(r'^excuses/submit/(?P<event_id>[0-9]+)/$', views.excuse_submit, name='excuse_submit'),
  
  url(r'^excuses/pending/$', views.excuse_pending, name='excuse_pending'),
  #url(r'^excuses/approve/(?P<excuse_id>[0-9]+)/$', views.excuse_approve, name='excuse_approve'),
  #url(r'^excuses/deny/(?P<excuse_id>[0-9]+)/$', views.excuse_deny, name='excuse_deny'),

]