from django.conf.urls import url
from django.conf.urls import include
from . import views

# Namespacing
app_name = 'attendance'

urlpatterns = [
  # All authentication views
  url('^', include('django.contrib.auth.urls')),

  # Homepage
  url(r'^$', views.index, name='index'),

  # Sister-related views
  url(r'^sister/$', views.personal_record, name='personal_record'),

  # Event-related views
  url(r'^events/$', views.events, name='events'),
  url(r'^events/(?P<event_id>[0-9]+)/$', views.event_details, name='event_details'),
  url(r'^events/(?P<event_id>[0-9]+)/activate/$', views.activate, name='activate'),
  url(r'^events/(?P<event_id>[0-9]+)/checkin/sisters/(?P<sister_id>[0-9]+)$', views.checkin_sister, name='checkin_sister'),

  #Excuse-related views
  url(r'^excuses/submit/(?P<event_id>[0-9]+)/$', views.excuse_submit, name='excuse_submit'),
  
  url(r'^excuses/pending/$', views.excuse_pending, name='excuse_pending'),
  url(r'^excuses/approve/(?P<excuse_id>[0-9]+)/$', views.excuse_approve, name='excuse_approve'),
  url(r'^excuses/deny/(?P<excuse_id>[0-9]+)/$', views.excuse_deny, name='excuse_deny'),

]