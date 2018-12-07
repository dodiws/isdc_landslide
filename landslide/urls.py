from .views import getLandslide
from django.conf.urls import include, patterns, url
from tastypie.api import Api

geoapi = Api(api_name='geoapi')

geoapi.register(getLandslide())

urlpatterns = [
    url(r'', include(geoapi.urls)),
    url(r'^getOverviewMaps/', include(patterns(
        'landslide.views',
        url(r'^landslideinfo$', 'getLandSlideInfoVillages', name='getLandSlideInfoVillages'),
    ))),
]
