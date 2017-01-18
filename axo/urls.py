"""axo URL Configuration

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/1.10/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  url(r'^$', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  url(r'^$', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.conf.urls import url, include
    2. Add a URL to urlpatterns:  url(r'^blog/', include('blog.urls'))
"""
from django.conf.urls import include, url
from django.contrib import admin
from django.contrib.auth import views as auth_views
from general import views as general_views
#from django.urls import reverse
from settings import LOGIN_REDIRECT_URL


urlpatterns = [

# All authentication views
#url('^', include('django.contrib.auth.urls')),
url(r'^login/', auth_views.login, name='login'),
url(r'^logout/', auth_views.logout, name='logout'),
url(r'^password_change/$',
    auth_views.password_change,
    {'post_change_redirect': LOGIN_REDIRECT_URL},
    name='password_change'),
url(r'^password_reset/$',
    auth_views.password_reset,
    name='password_reset'),
url(r'^password_reset_done/$',
    auth_views.password_reset_done,
    name='password_reset_done'),
url(r'^reset/(?P<uidb64>[0-9A-Za-z_\-]+)/(?P<token>[0-9A-Za-z]{1,13}-[0-9A-Za-z]{1,20})/$',
    auth_views.password_reset_confirm,
    {'post_reset_redirect': LOGIN_REDIRECT_URL},
    name='password_reset_confirm'),

url(r'^polls/', include('polls.urls')),
url(r'^admin/', admin.site.urls),
url(r'^attendance/', include('attendance.urls')),
url(r'^', include('general.urls')),
url(r'^elections/', include('elections.urls')),
]
