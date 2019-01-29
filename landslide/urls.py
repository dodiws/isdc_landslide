from .views import getLandslide, LandslideInfoVillages
from django.conf.urls import include, patterns, url
from tastypie.api import Api

geoapi = Api(api_name='geoapi')

geoapi.register(getLandslide())

# this var will be imported by geonode.urls and registered by getoverviewmaps api
GETOVERVIEWMAPS_APIOBJ = [
    LandslideInfoVillages(),
]

urlpatterns = [
    url(r'', include(geoapi.urls)),
    url(r'^getOverviewMaps/', include(patterns(
        'landslide.views',
        url(r'^landslideinfo$', 'getLandSlideInfoVillages', name='getLandSlideInfoVillages'),
    ))),
]
