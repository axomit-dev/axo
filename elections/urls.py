from django.conf.urls import url, include
from . import views

# Namespacing
app_name = 'elections'

urlpatterns = [
  # Homepage
  url(r'^$', views.index, name='index'),

  url(r'^ois/submission/$', views.ois_submission, name='ois_submission'),
  url(r'^ois/results/$', views.ois_results, name='ois_results'),
 
  url(r'^loi/submission/$', views.loi_submission, name='loi_submission'),
  url(r'^loi/results/$', views.loi_results, name='loi_results'),

  url(r'^slating/submission/$', views.slating_submission, name='slating_submission'),
  url(r'^slating/results/$', views.slating_results, name='slating_results'),

  url(r'^voting/submission/$', views.voting_submission, name='voting_submission'),
  url(r'^voting/results/$', views.voting_results, name='voting_results'),

]