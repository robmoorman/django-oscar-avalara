from django.conf.urls import include, url
from django.contrib import admin
from oscar.app import application


urlpatterns = [
    url(r'^admin/', include(admin.site.urls)),
    url(r'', include(application.urls)),
]
