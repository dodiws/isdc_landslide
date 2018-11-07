from .views import (
    getLandslide
)
from django.conf.urls import include, patterns, url
from tastypie.api import Api

geoapi = Api(api_name='geoapi')

geoapi.register(getLandslide())

urlpatterns_getoverviewmaps = patterns(
    'landslide.views',
    url(r'^landslideinfo$', 'getLandSlideInfoVillages', name='getLandSlideInfoVillages'),
)

urlpatterns = [
    # api
    url(r'', include(geoapi.urls)),

    url(r'^getOverviewMaps/', include(urlpatterns_getoverviewmaps)),
]
