from geodb.models import (
	# AfgFldzonea100KRiskLandcoverPop,
	AfgLndcrva,
	# AfgAdmbndaAdm1,
	# AfgAdmbndaAdm2,
	# AfgFldzonea100KRiskMitigatedAreas,
	# AfgAvsa,
	# Forcastedvalue,
	# AfgShedaLvl4,
	# districtsummary,
	provincesummary,
	# basinsummary,
	# AfgPpla,
	# tempCurrentSC,
	# earthquake_events,
	# earthquake_shakemap,
	# villagesummaryEQ,
	# AfgPplp,
	# AfgSnowaAverageExtent,
	# AfgCaptPpl,
	# AfgAirdrmp,
	# AfgHltfac,
	# forecastedLastUpdate,
	# AfgCaptGmscvr,
	# AfgEqtUnkPplEqHzd,
	# Glofasintegrated,
	# AfgBasinLvl4GlofasPoint,
	# AfgPpltDemographics,
	AfgLspAffpplp,
	# AfgMettClim1KmChelsaBioclim,
	# AfgMettClim1KmWorldclimBioclim2050Rpc26,
	# AfgMettClim1KmWorldclimBioclim2050Rpc45,
	# AfgMettClim1KmWorldclimBioclim2050Rpc85,
	# AfgMettClim1KmWorldclimBioclim2070Rpc26,
	# AfgMettClim1KmWorldclimBioclim2070Rpc45,
	# AfgMettClim1KmWorldclimBioclim2070Rpc85,
	# AfgMettClimperc1KmChelsaPrec,
	# AfgMettClimtemp1KmChelsaTempavg,
	# AfgMettClimtemp1KmChelsaTempmax,
	# AfgMettClimtemp1KmChelsaTempmin
	)
# from .models import (
#     earthquake_events,
#     earthquake_shakemap,
#     villagesummaryEQ,
#     AfgEqtUnkPplEqHzd,
#     )
from geodb.geo_calc import (
	getBaseline,
	getCommonUse,
	# getFloodForecastBySource,
	# getFloodForecastMatrix,
	getGeoJson,
	# getProvinceSummary_glofas,
	getProvinceSummary,
	# getRawBaseLine,
	# getRawFloodRisk,
	# getSettlementAtFloodRisk,
	getShortCutData,
	getTotalArea,
	getTotalBuildings,
	getTotalPop,
	getTotalSettlement,
	# getRiskNumber,
	)
from geodb.views import (
	getCommonVillageData,
)
from django.contrib.gis.geos import Point
# from django.contrib.gis.utils import LayerMapping
# from django.core.serializers.json import DjangoJSONEncoder
from django.db import connection, connections
from django.shortcuts import render_to_response
from django.shortcuts import render, get_object_or_404
from django.template import RequestContext
from django.utils.translation import ugettext as _
# from geodb.usgs_comcat import getContents, getUTCTimeStamp
# from geodb.views import GS_TMP_DIR, gdal_path, cleantmpfile, update_progress, getKeyCustom
from geonode.utils import include_section, none_to_zero, query_to_dicts, RawSQL_nogroupby, dict_ext, list_ext
from graphos.renderers import flot, gchart
from graphos.sources.simple import SimpleDataSource
# from itertools import cycle, izip
from matrix.models import matrix
# from tastypie import fields
# from tastypie.authorization import DjangoAuthorization
from tastypie.cache import SimpleCache
from tastypie.resources import ModelResource, Resource
from tastypie.serializers import Serializer
# from tempfile import mktemp
from zipfile import ZipFile
import csv, os
import datetime, re
import json
# import subprocess
import time, sys
import urllib
from geonode.maps.views import _resolve_map, _PERMISSION_MSG_VIEW

from urlparse import urlparse
# import urllib2
from landslide.enumerations import LANDSLIDE_TYPES, LANDSLIDE_TYPES_ORDER, LANDSLIDE_INDEX_TYPES, LANDSLIDE_INDEX_TYPES_ORDER
from django.conf.urls import url
from tastypie.utils import trailing_slash
from tastypie.authentication import BasicAuthentication, SessionAuthentication, OAuthAuthentication

def get_dashboard_meta():
	return {
		'pages': [
			{
				'name': 'landslide',
				'function': dashboard_landslide, 
				'template': 'dash_landslide.html',
				'menutitle': 'Landslide',
			},
		],
		'menutitle': 'Landslide',
	}

# def getQuickOverview(request, filterLock, flag, code, includes=[], excludes=[]):
# 	response = {}
# 	response.update(getLandslideRisk(request, filterLock, flag, code, includes=['lsi_immap']))
# 	return response

# moved from geodb.geo_calc

def getLandslideRiskChild(filterLock, flag, code):
	sql = ''
	if flag=='entireAfg':
		sql = "select afg_lsp_affpplp.prov_code as code, afg_pplp.prov_na_en as na_en, \
				coalesce(round(sum(case \
				 when afg_lsp_affpplp.lsi_immap >= 7 then afg_pplp.vuid_population \
				end)),0) as lsi_immap_very_high, \
				coalesce(round(sum(case \
				 when afg_lsp_affpplp.lsi_immap >= 5 and afg_lsp_affpplp.lsi_immap < 7 then afg_pplp.vuid_population \
				end)),0) as lsi_immap_high, \
				coalesce(round(sum(case \
				 when afg_lsp_affpplp.lsi_immap >= 4 and afg_lsp_affpplp.lsi_immap < 5 then afg_pplp.vuid_population \
				end)),0) as lsi_immap_moderate, \
				coalesce(round(sum(case \
				 when afg_lsp_affpplp.lsi_immap >= 2 and afg_lsp_affpplp.lsi_immap < 4 then afg_pplp.vuid_population \
				end)),0) as lsi_immap_low, \
				coalesce(round(sum(case \
				 when afg_lsp_affpplp.lsi_immap >= 1 and afg_lsp_affpplp.lsi_immap < 2 then afg_pplp.vuid_population \
				end)),0) as lsi_immap_very_low, \
				coalesce(round(sum(case \
				 when afg_lsp_affpplp.lsi_ku >= 7 then afg_pplp.vuid_population \
				end)),0) as lsi_ku_very_high, \
				coalesce(round(sum(case \
				 when afg_lsp_affpplp.lsi_ku >= 5 and afg_lsp_affpplp.lsi_ku < 7 then afg_pplp.vuid_population \
				end)),0) as lsi_ku_high, \
				coalesce(round(sum(case \
				 when afg_lsp_affpplp.lsi_ku >= 4 and afg_lsp_affpplp.lsi_ku < 5 then afg_pplp.vuid_population \
				end)),0) as lsi_ku_moderate, \
				coalesce(round(sum(case \
				 when afg_lsp_affpplp.lsi_ku >= 2 and afg_lsp_affpplp.lsi_ku < 4 then afg_pplp.vuid_population \
				end)),0) as lsi_ku_low, \
				coalesce(round(sum(case \
				 when afg_lsp_affpplp.lsi_ku >= 1 and afg_lsp_affpplp.lsi_ku < 2 then afg_pplp.vuid_population \
				end)),0) as lsi_ku_very_low, \
				coalesce(round(sum(case \
				 when afg_lsp_affpplp.ls_s1_wb >= 7 then afg_pplp.vuid_population \
				end)),0) as ls_s1_wb_very_high, \
				coalesce(round(sum(case \
				 when afg_lsp_affpplp.ls_s1_wb >= 5 and afg_lsp_affpplp.ls_s1_wb < 7 then afg_pplp.vuid_population \
				end)),0) as ls_s1_wb_high, \
				coalesce(round(sum(case \
				 when afg_lsp_affpplp.ls_s1_wb >= 4 and afg_lsp_affpplp.ls_s1_wb < 5 then afg_pplp.vuid_population \
				end)),0) as ls_s1_wb_moderate, \
				coalesce(round(sum(case  \
				 when afg_lsp_affpplp.ls_s1_wb >= 2 and afg_lsp_affpplp.ls_s1_wb < 4 then afg_pplp.vuid_population \
				end)),0) as ls_s1_wb_low, \
				coalesce(round(sum(case \
				 when afg_lsp_affpplp.ls_s1_wb >= 1 and afg_lsp_affpplp.ls_s1_wb < 2 then afg_pplp.vuid_population \
				end)),0) as ls_s1_wb_very_low, \
				coalesce(round(sum(case \
				 when afg_lsp_affpplp.ls_s2_wb >= 7 then afg_pplp.vuid_population \
				end)),0) as ls_s2_wb_very_high, \
				coalesce(round(sum(case \
				 when afg_lsp_affpplp.ls_s2_wb >= 5 and afg_lsp_affpplp.ls_s2_wb < 7 then afg_pplp.vuid_population \
				end)),0) as ls_s2_wb_high, \
				coalesce(round(sum(case \
				 when afg_lsp_affpplp.ls_s2_wb >= 4 and afg_lsp_affpplp.ls_s2_wb < 5 then afg_pplp.vuid_population \
				end)),0) as ls_s2_wb_moderate, \
				coalesce(round(sum(case \
				 when afg_lsp_affpplp.ls_s2_wb >= 2 and afg_lsp_affpplp.ls_s2_wb < 4 then afg_pplp.vuid_population \
				end)),0) as ls_s2_wb_low, \
				coalesce(round(sum(case \
				 when afg_lsp_affpplp.ls_s2_wb >= 1 and afg_lsp_affpplp.ls_s2_wb < 2 then afg_pplp.vuid_population \
				end)),0) as ls_s2_wb_very_low, \
				coalesce(round(sum(case \
				 when afg_lsp_affpplp.ls_s3_wb >= 7 then afg_pplp.vuid_population \
				end)),0) as ls_s3_wb_very_high, \
				coalesce(round(sum(case \
				 when afg_lsp_affpplp.ls_s3_wb >= 5 and afg_lsp_affpplp.ls_s3_wb < 7 then afg_pplp.vuid_population \
				end)),0) as ls_s3_wb_high, \
				coalesce(round(sum(case \
				 when afg_lsp_affpplp.ls_s3_wb >= 4 and afg_lsp_affpplp.ls_s3_wb < 5 then afg_pplp.vuid_population \
				end)),0) as ls_s3_wb_moderate, \
				coalesce(round(sum(case  \
				 when afg_lsp_affpplp.ls_s3_wb >= 2 and afg_lsp_affpplp.ls_s3_wb < 4 then afg_pplp.vuid_population \
				end)),0) as ls_s3_wb_low, \
				coalesce(round(sum(case \
				 when afg_lsp_affpplp.ls_s3_wb >= 1 and afg_lsp_affpplp.ls_s3_wb < 2 then afg_pplp.vuid_population \
				end)),0) as ls_s3_wb_very_low    \
				from afg_lsp_affpplp \
				inner join afg_pplp on afg_lsp_affpplp.vuid=afg_pplp.vuid group by 1,2 order by 2"

	elif flag =='currentProvince':
		if len(str(code)) == 2:
			ff0001 =  "afg_pplp.prov_code_1  = '"+str(code)+"'"
			sql = "select afg_lsp_affpplp.dist_code as code, afg_pplp.dist_na_en as na_en, \
					coalesce(round(sum(case \
					 when afg_lsp_affpplp.lsi_immap >= 7 then afg_pplp.vuid_population \
					end)),0) as lsi_immap_very_high, \
					coalesce(round(sum(case \
					 when afg_lsp_affpplp.lsi_immap >= 5 and afg_lsp_affpplp.lsi_immap < 7 then afg_pplp.vuid_population \
					end)),0) as lsi_immap_high, \
					coalesce(round(sum(case \
					 when afg_lsp_affpplp.lsi_immap >= 4 and afg_lsp_affpplp.lsi_immap < 5 then afg_pplp.vuid_population \
					end)),0) as lsi_immap_moderate, \
					coalesce(round(sum(case \
					 when afg_lsp_affpplp.lsi_immap >= 2 and afg_lsp_affpplp.lsi_immap < 4 then afg_pplp.vuid_population \
					end)),0) as lsi_immap_low, \
					coalesce(round(sum(case \
					 when afg_lsp_affpplp.lsi_immap >= 1 and afg_lsp_affpplp.lsi_immap < 2 then afg_pplp.vuid_population \
					end)),0) as lsi_immap_very_low, \
					coalesce(round(sum(case \
					 when afg_lsp_affpplp.lsi_ku >= 7 then afg_pplp.vuid_population \
					end)),0) as lsi_ku_very_high, \
					coalesce(round(sum(case \
					 when afg_lsp_affpplp.lsi_ku >= 5 and afg_lsp_affpplp.lsi_ku < 7 then afg_pplp.vuid_population \
					end)),0) as lsi_ku_high, \
					coalesce(round(sum(case \
					 when afg_lsp_affpplp.lsi_ku >= 4 and afg_lsp_affpplp.lsi_ku < 5 then afg_pplp.vuid_population \
					end)),0) as lsi_ku_moderate, \
					coalesce(round(sum(case \
					 when afg_lsp_affpplp.lsi_ku >= 2 and afg_lsp_affpplp.lsi_ku < 4 then afg_pplp.vuid_population \
					end)),0) as lsi_ku_low, \
					coalesce(round(sum(case \
					 when afg_lsp_affpplp.lsi_ku >= 1 and afg_lsp_affpplp.lsi_ku < 2 then afg_pplp.vuid_population \
					end)),0) as lsi_ku_very_low, \
					coalesce(round(sum(case \
					 when afg_lsp_affpplp.ls_s1_wb >= 7 then afg_pplp.vuid_population \
					end)),0) as ls_s1_wb_very_high, \
					coalesce(round(sum(case \
					 when afg_lsp_affpplp.ls_s1_wb >= 5 and afg_lsp_affpplp.ls_s1_wb < 7 then afg_pplp.vuid_population \
					end)),0) as ls_s1_wb_high, \
					coalesce(round(sum(case \
					 when afg_lsp_affpplp.ls_s1_wb >= 4 and afg_lsp_affpplp.ls_s1_wb < 5 then afg_pplp.vuid_population \
					end)),0) as ls_s1_wb_moderate, \
					coalesce(round(sum(case  \
					 when afg_lsp_affpplp.ls_s1_wb >= 2 and afg_lsp_affpplp.ls_s1_wb < 4 then afg_pplp.vuid_population \
					end)),0) as ls_s1_wb_low, \
					coalesce(round(sum(case \
					 when afg_lsp_affpplp.ls_s1_wb >= 1 and afg_lsp_affpplp.ls_s1_wb < 2 then afg_pplp.vuid_population \
					end)),0) as ls_s1_wb_very_low, \
					coalesce(round(sum(case \
					 when afg_lsp_affpplp.ls_s2_wb >= 7 then afg_pplp.vuid_population \
					end)),0) as ls_s2_wb_very_high, \
					coalesce(round(sum(case \
					 when afg_lsp_affpplp.ls_s2_wb >= 5 and afg_lsp_affpplp.ls_s2_wb < 7 then afg_pplp.vuid_population \
					end)),0) as ls_s2_wb_high, \
					coalesce(round(sum(case \
					 when afg_lsp_affpplp.ls_s2_wb >= 4 and afg_lsp_affpplp.ls_s2_wb < 5 then afg_pplp.vuid_population \
					end)),0) as ls_s2_wb_moderate, \
					coalesce(round(sum(case \
					 when afg_lsp_affpplp.ls_s2_wb >= 2 and afg_lsp_affpplp.ls_s2_wb < 4 then afg_pplp.vuid_population \
					end)),0) as ls_s2_wb_low, \
					coalesce(round(sum(case \
					 when afg_lsp_affpplp.ls_s2_wb >= 1 and afg_lsp_affpplp.ls_s2_wb < 2 then afg_pplp.vuid_population \
					end)),0) as ls_s2_wb_very_low, \
					coalesce(round(sum(case \
					 when afg_lsp_affpplp.ls_s3_wb >= 7 then afg_pplp.vuid_population \
					end)),0) as ls_s3_wb_very_high, \
					coalesce(round(sum(case \
					 when afg_lsp_affpplp.ls_s3_wb >= 5 and afg_lsp_affpplp.ls_s3_wb < 7 then afg_pplp.vuid_population \
					end)),0) as ls_s3_wb_high, \
					coalesce(round(sum(case \
					 when afg_lsp_affpplp.ls_s3_wb >= 4 and afg_lsp_affpplp.ls_s3_wb < 5 then afg_pplp.vuid_population \
					end)),0) as ls_s3_wb_moderate, \
					coalesce(round(sum(case  \
					 when afg_lsp_affpplp.ls_s3_wb >= 2 and afg_lsp_affpplp.ls_s3_wb < 4 then afg_pplp.vuid_population \
					end)),0) as ls_s3_wb_low, \
					coalesce(round(sum(case \
					 when afg_lsp_affpplp.ls_s3_wb >= 1 and afg_lsp_affpplp.ls_s3_wb < 2 then afg_pplp.vuid_population \
					end)),0) as ls_s3_wb_very_low    \
					from afg_lsp_affpplp \
					inner join afg_pplp on afg_lsp_affpplp.vuid=afg_pplp.vuid \
					where " +  ff0001  + " group by 1,2 order by 2"

	response = []

	if sql != '' :
		cursor = connections['geodb'].cursor()
		row = query_to_dicts(cursor, sql)

		for i in row:
			response.append(i)

		cursor.close()

	return response

def getLandslideRisk(request, filterLock, flag, code, includes=[], excludes=[], response=dict_ext()):
	# response = dict_ext()
	# if include_section('getCommonUse', includes, excludes):
	#     response = getCommonUse(request, flag, code)
	if include_section('baseline', includes, excludes):
		# targetBase = AfgLndcrva.objects.all()

		response['baseline'] = response.pathget('cache','getBaseline','baseline') or getBaseline(request, filterLock, flag, code, includes=['pop_lc','building_lc'])
		# if flag not in ['entireAfg','currentProvince']:
		#     response['Population']=getTotalPop(filterLock, flag, code, targetBase)
		#     response['Area']=getTotalArea(filterLock, flag, code, targetBase)
		#     response['Buildings']=getTotalBuildings(filterLock, flag, code, targetBase)
		#     response['settlement']=getTotalSettlement(filterLock, flag, code, targetBase)
		# else :
		#     tempData = getShortCutData(flag,code)
		#     response['Population']= tempData['Population']
		#     response['Area']= tempData['Area']
		#     response['Buildings']= tempData['total_buildings']
		#     response['settlement']= tempData['settlements']

	if include_section('lc_child', includes, excludes):
		response['lc_child'] = getLandslideRiskChild(filterLock, flag, code)

	if include_section('lsi', includes, excludes):
		if flag=='entireAfg':
			sql = "select \
					coalesce(round(sum(case \
					 when afg_lsp_affpplp.lsi_immap >= 7 then afg_pplp.vuid_population \
					end)),0) as lsi_immap_very_high, \
					coalesce(round(sum(case \
					 when afg_lsp_affpplp.lsi_immap >= 5 and afg_lsp_affpplp.lsi_immap < 7 then afg_pplp.vuid_population \
					end)),0) as lsi_immap_high, \
					coalesce(round(sum(case \
					 when afg_lsp_affpplp.lsi_immap >= 4 and afg_lsp_affpplp.lsi_immap < 5 then afg_pplp.vuid_population \
					end)),0) as lsi_immap_moderate, \
					coalesce(round(sum(case \
					 when afg_lsp_affpplp.lsi_immap >= 2 and afg_lsp_affpplp.lsi_immap < 4 then afg_pplp.vuid_population \
					end)),0) as lsi_immap_low, \
					coalesce(round(sum(case \
					 when afg_lsp_affpplp.lsi_immap >= 1 and afg_lsp_affpplp.lsi_immap < 2 then afg_pplp.vuid_population \
					end)),0) as lsi_immap_very_low, \
					coalesce(round(sum(case \
					 when afg_lsp_affpplp.lsi_ku >= 7 then afg_pplp.vuid_population \
					end)),0) as lsi_ku_very_high, \
					coalesce(round(sum(case \
					 when afg_lsp_affpplp.lsi_ku >= 5 and afg_lsp_affpplp.lsi_ku < 7 then afg_pplp.vuid_population \
					end)),0) as lsi_ku_high, \
					coalesce(round(sum(case \
					 when afg_lsp_affpplp.lsi_ku >= 4 and afg_lsp_affpplp.lsi_ku < 5 then afg_pplp.vuid_population \
					end)),0) as lsi_ku_moderate, \
					coalesce(round(sum(case \
					 when afg_lsp_affpplp.lsi_ku >= 2 and afg_lsp_affpplp.lsi_ku < 4 then afg_pplp.vuid_population \
					end)),0) as lsi_ku_low, \
					coalesce(round(sum(case \
					 when afg_lsp_affpplp.lsi_ku >= 1 and afg_lsp_affpplp.lsi_ku < 2 then afg_pplp.vuid_population \
					end)),0) as lsi_ku_very_low, \
					coalesce(round(sum(case \
					 when afg_lsp_affpplp.ls_s1_wb >= 7 then afg_pplp.vuid_population \
					end)),0) as ls_s1_wb_very_high, \
					coalesce(round(sum(case \
					 when afg_lsp_affpplp.ls_s1_wb >= 5 and afg_lsp_affpplp.ls_s1_wb < 7 then afg_pplp.vuid_population \
					end)),0) as ls_s1_wb_high, \
					coalesce(round(sum(case \
					 when afg_lsp_affpplp.ls_s1_wb >= 4 and afg_lsp_affpplp.ls_s1_wb < 5 then afg_pplp.vuid_population \
					end)),0) as ls_s1_wb_moderate, \
					coalesce(round(sum(case  \
					 when afg_lsp_affpplp.ls_s1_wb >= 2 and afg_lsp_affpplp.ls_s1_wb < 4 then afg_pplp.vuid_population \
					end)),0) as ls_s1_wb_low, \
					coalesce(round(sum(case \
					 when afg_lsp_affpplp.ls_s1_wb >= 1 and afg_lsp_affpplp.ls_s1_wb < 2 then afg_pplp.vuid_population \
					end)),0) as ls_s1_wb_very_low, \
					coalesce(round(sum(case \
					 when afg_lsp_affpplp.ls_s2_wb >= 7 then afg_pplp.vuid_population \
					end)),0) as ls_s2_wb_very_high, \
					coalesce(round(sum(case \
					 when afg_lsp_affpplp.ls_s2_wb >= 5 and afg_lsp_affpplp.ls_s2_wb < 7 then afg_pplp.vuid_population \
					end)),0) as ls_s2_wb_high, \
					coalesce(round(sum(case \
					 when afg_lsp_affpplp.ls_s2_wb >= 4 and afg_lsp_affpplp.ls_s2_wb < 5 then afg_pplp.vuid_population \
					end)),0) as ls_s2_wb_moderate, \
					coalesce(round(sum(case \
					 when afg_lsp_affpplp.ls_s2_wb >= 2 and afg_lsp_affpplp.ls_s2_wb < 4 then afg_pplp.vuid_population \
					end)),0) as ls_s2_wb_low, \
					coalesce(round(sum(case \
					 when afg_lsp_affpplp.ls_s2_wb >= 1 and afg_lsp_affpplp.ls_s2_wb < 2 then afg_pplp.vuid_population \
					end)),0) as ls_s2_wb_very_low, \
					coalesce(round(sum(case \
					 when afg_lsp_affpplp.ls_s3_wb >= 7 then afg_pplp.vuid_population \
					end)),0) as ls_s3_wb_very_high, \
					coalesce(round(sum(case \
					 when afg_lsp_affpplp.ls_s3_wb >= 5 and afg_lsp_affpplp.ls_s3_wb < 7 then afg_pplp.vuid_population \
					end)),0) as ls_s3_wb_high, \
					coalesce(round(sum(case \
					 when afg_lsp_affpplp.ls_s3_wb >= 4 and afg_lsp_affpplp.ls_s3_wb < 5 then afg_pplp.vuid_population \
					end)),0) as ls_s3_wb_moderate, \
					coalesce(round(sum(case  \
					 when afg_lsp_affpplp.ls_s3_wb >= 2 and afg_lsp_affpplp.ls_s3_wb < 4 then afg_pplp.vuid_population \
					end)),0) as ls_s3_wb_low, \
					coalesce(round(sum(case \
					 when afg_lsp_affpplp.ls_s3_wb >= 1 and afg_lsp_affpplp.ls_s3_wb < 2 then afg_pplp.vuid_population \
					end)),0) as ls_s3_wb_very_low    \
					from afg_lsp_affpplp \
					inner join afg_pplp on afg_lsp_affpplp.vuid=afg_pplp.vuid"

		elif flag =='currentProvince':
			if len(str(code)) > 2:
				ff0001 =  "afg_pplp.dist_code  = '"+str(code)+"'"
			else :
				ff0001 =  "afg_pplp.prov_code_1  = '"+str(code)+"'"

			sql = "select \
					coalesce(round(sum(case \
					 when afg_lsp_affpplp.lsi_immap >= 7 then afg_pplp.vuid_population \
					end)),0) as lsi_immap_very_high, \
					coalesce(round(sum(case \
					 when afg_lsp_affpplp.lsi_immap >= 5 and afg_lsp_affpplp.lsi_immap < 7 then afg_pplp.vuid_population \
					end)),0) as lsi_immap_high, \
					coalesce(round(sum(case \
					 when afg_lsp_affpplp.lsi_immap >= 4 and afg_lsp_affpplp.lsi_immap < 5 then afg_pplp.vuid_population \
					end)),0) as lsi_immap_moderate, \
					coalesce(round(sum(case \
					 when afg_lsp_affpplp.lsi_immap >= 2 and afg_lsp_affpplp.lsi_immap < 4 then afg_pplp.vuid_population \
					end)),0) as lsi_immap_low, \
					coalesce(round(sum(case \
					 when afg_lsp_affpplp.lsi_immap >= 1 and afg_lsp_affpplp.lsi_immap < 2 then afg_pplp.vuid_population \
					end)),0) as lsi_immap_very_low, \
					coalesce(round(sum(case \
					 when afg_lsp_affpplp.lsi_ku >= 7 then afg_pplp.vuid_population \
					end)),0) as lsi_ku_very_high, \
					coalesce(round(sum(case \
					 when afg_lsp_affpplp.lsi_ku >= 5 and afg_lsp_affpplp.lsi_ku < 7 then afg_pplp.vuid_population \
					end)),0) as lsi_ku_high, \
					coalesce(round(sum(case \
					 when afg_lsp_affpplp.lsi_ku >= 4 and afg_lsp_affpplp.lsi_ku < 5 then afg_pplp.vuid_population \
					end)),0) as lsi_ku_moderate, \
					coalesce(round(sum(case \
					 when afg_lsp_affpplp.lsi_ku >= 2 and afg_lsp_affpplp.lsi_ku < 4 then afg_pplp.vuid_population \
					end)),0) as lsi_ku_low, \
					coalesce(round(sum(case \
					 when afg_lsp_affpplp.lsi_ku >= 1 and afg_lsp_affpplp.lsi_ku < 2 then afg_pplp.vuid_population \
					end)),0) as lsi_ku_very_low, \
					coalesce(round(sum(case \
					 when afg_lsp_affpplp.ls_s1_wb >= 7 then afg_pplp.vuid_population \
					end)),0) as ls_s1_wb_very_high, \
					coalesce(round(sum(case \
					 when afg_lsp_affpplp.ls_s1_wb >= 5 and afg_lsp_affpplp.ls_s1_wb < 7 then afg_pplp.vuid_population \
					end)),0) as ls_s1_wb_high, \
					coalesce(round(sum(case \
					 when afg_lsp_affpplp.ls_s1_wb >= 4 and afg_lsp_affpplp.ls_s1_wb < 5 then afg_pplp.vuid_population \
					end)),0) as ls_s1_wb_moderate, \
					coalesce(round(sum(case  \
					 when afg_lsp_affpplp.ls_s1_wb >= 2 and afg_lsp_affpplp.ls_s1_wb < 4 then afg_pplp.vuid_population \
					end)),0) as ls_s1_wb_low, \
					coalesce(round(sum(case \
					 when afg_lsp_affpplp.ls_s1_wb >= 1 and afg_lsp_affpplp.ls_s1_wb < 2 then afg_pplp.vuid_population \
					end)),0) as ls_s1_wb_very_low, \
					coalesce(round(sum(case \
					 when afg_lsp_affpplp.ls_s2_wb >= 7 then afg_pplp.vuid_population \
					end)),0) as ls_s2_wb_very_high, \
					coalesce(round(sum(case \
					 when afg_lsp_affpplp.ls_s2_wb >= 5 and afg_lsp_affpplp.ls_s2_wb < 7 then afg_pplp.vuid_population \
					end)),0) as ls_s2_wb_high, \
					coalesce(round(sum(case \
					 when afg_lsp_affpplp.ls_s2_wb >= 4 and afg_lsp_affpplp.ls_s2_wb < 5 then afg_pplp.vuid_population \
					end)),0) as ls_s2_wb_moderate, \
					coalesce(round(sum(case \
					 when afg_lsp_affpplp.ls_s2_wb >= 2 and afg_lsp_affpplp.ls_s2_wb < 4 then afg_pplp.vuid_population \
					end)),0) as ls_s2_wb_low, \
					coalesce(round(sum(case \
					 when afg_lsp_affpplp.ls_s2_wb >= 1 and afg_lsp_affpplp.ls_s2_wb < 2 then afg_pplp.vuid_population \
					end)),0) as ls_s2_wb_very_low, \
					coalesce(round(sum(case \
					 when afg_lsp_affpplp.ls_s3_wb >= 7 then afg_pplp.vuid_population \
					end)),0) as ls_s3_wb_very_high, \
					coalesce(round(sum(case \
					 when afg_lsp_affpplp.ls_s3_wb >= 5 and afg_lsp_affpplp.ls_s3_wb < 7 then afg_pplp.vuid_population \
					end)),0) as ls_s3_wb_high, \
					coalesce(round(sum(case \
					 when afg_lsp_affpplp.ls_s3_wb >= 4 and afg_lsp_affpplp.ls_s3_wb < 5 then afg_pplp.vuid_population \
					end)),0) as ls_s3_wb_moderate, \
					coalesce(round(sum(case  \
					 when afg_lsp_affpplp.ls_s3_wb >= 2 and afg_lsp_affpplp.ls_s3_wb < 4 then afg_pplp.vuid_population \
					end)),0) as ls_s3_wb_low, \
					coalesce(round(sum(case \
					 when afg_lsp_affpplp.ls_s3_wb >= 1 and afg_lsp_affpplp.ls_s3_wb < 2 then afg_pplp.vuid_population \
					end)),0) as ls_s3_wb_very_low    \
					from afg_lsp_affpplp \
					inner join afg_pplp on afg_lsp_affpplp.vuid=afg_pplp.vuid \
					where " +  ff0001

		elif flag =='drawArea':
			sql = "select \
					coalesce(round(sum(case \
					 when afg_lsp_affpplp.lsi_immap >= 7 then afg_pplp.vuid_population \
					end)),0) as lsi_immap_very_high, \
					coalesce(round(sum(case \
					 when afg_lsp_affpplp.lsi_immap >= 5 and afg_lsp_affpplp.lsi_immap < 7 then afg_pplp.vuid_population \
					end)),0) as lsi_immap_high, \
					coalesce(round(sum(case \
					 when afg_lsp_affpplp.lsi_immap >= 4 and afg_lsp_affpplp.lsi_immap < 5 then afg_pplp.vuid_population \
					end)),0) as lsi_immap_moderate, \
					coalesce(round(sum(case \
					 when afg_lsp_affpplp.lsi_immap >= 2 and afg_lsp_affpplp.lsi_immap < 4 then afg_pplp.vuid_population \
					end)),0) as lsi_immap_low, \
					coalesce(round(sum(case \
					 when afg_lsp_affpplp.lsi_immap >= 1 and afg_lsp_affpplp.lsi_immap < 2 then afg_pplp.vuid_population \
					end)),0) as lsi_immap_very_low, \
					coalesce(round(sum(case \
					 when afg_lsp_affpplp.lsi_ku >= 7 then afg_pplp.vuid_population \
					end)),0) as lsi_ku_very_high, \
					coalesce(round(sum(case \
					 when afg_lsp_affpplp.lsi_ku >= 5 and afg_lsp_affpplp.lsi_ku < 7 then afg_pplp.vuid_population \
					end)),0) as lsi_ku_high, \
					coalesce(round(sum(case \
					 when afg_lsp_affpplp.lsi_ku >= 4 and afg_lsp_affpplp.lsi_ku < 5 then afg_pplp.vuid_population \
					end)),0) as lsi_ku_moderate, \
					coalesce(round(sum(case \
					 when afg_lsp_affpplp.lsi_ku >= 2 and afg_lsp_affpplp.lsi_ku < 4 then afg_pplp.vuid_population \
					end)),0) as lsi_ku_low, \
					coalesce(round(sum(case \
					 when afg_lsp_affpplp.lsi_ku >= 1 and afg_lsp_affpplp.lsi_ku < 2 then afg_pplp.vuid_population \
					end)),0) as lsi_ku_very_low, \
					coalesce(round(sum(case \
					 when afg_lsp_affpplp.ls_s1_wb >= 7 then afg_pplp.vuid_population \
					end)),0) as ls_s1_wb_very_high, \
					coalesce(round(sum(case \
					 when afg_lsp_affpplp.ls_s1_wb >= 5 and afg_lsp_affpplp.ls_s1_wb < 7 then afg_pplp.vuid_population \
					end)),0) as ls_s1_wb_high, \
					coalesce(round(sum(case \
					 when afg_lsp_affpplp.ls_s1_wb >= 4 and afg_lsp_affpplp.ls_s1_wb < 5 then afg_pplp.vuid_population \
					end)),0) as ls_s1_wb_moderate, \
					coalesce(round(sum(case  \
					 when afg_lsp_affpplp.ls_s1_wb >= 2 and afg_lsp_affpplp.ls_s1_wb < 4 then afg_pplp.vuid_population \
					end)),0) as ls_s1_wb_low, \
					coalesce(round(sum(case \
					 when afg_lsp_affpplp.ls_s1_wb >= 1 and afg_lsp_affpplp.ls_s1_wb < 2 then afg_pplp.vuid_population \
					end)),0) as ls_s1_wb_very_low, \
					coalesce(round(sum(case \
					 when afg_lsp_affpplp.ls_s2_wb >= 7 then afg_pplp.vuid_population \
					end)),0) as ls_s2_wb_very_high, \
					coalesce(round(sum(case \
					 when afg_lsp_affpplp.ls_s2_wb >= 5 and afg_lsp_affpplp.ls_s2_wb < 7 then afg_pplp.vuid_population \
					end)),0) as ls_s2_wb_high, \
					coalesce(round(sum(case \
					 when afg_lsp_affpplp.ls_s2_wb >= 4 and afg_lsp_affpplp.ls_s2_wb < 5 then afg_pplp.vuid_population \
					end)),0) as ls_s2_wb_moderate, \
					coalesce(round(sum(case \
					 when afg_lsp_affpplp.ls_s2_wb >= 2 and afg_lsp_affpplp.ls_s2_wb < 4 then afg_pplp.vuid_population \
					end)),0) as ls_s2_wb_low, \
					coalesce(round(sum(case \
					 when afg_lsp_affpplp.ls_s2_wb >= 1 and afg_lsp_affpplp.ls_s2_wb < 2 then afg_pplp.vuid_population \
					end)),0) as ls_s2_wb_very_low, \
					coalesce(round(sum(case \
					 when afg_lsp_affpplp.ls_s3_wb >= 7 then afg_pplp.vuid_population \
					end)),0) as ls_s3_wb_very_high, \
					coalesce(round(sum(case \
					 when afg_lsp_affpplp.ls_s3_wb >= 5 and afg_lsp_affpplp.ls_s3_wb < 7 then afg_pplp.vuid_population \
					end)),0) as ls_s3_wb_high, \
					coalesce(round(sum(case \
					 when afg_lsp_affpplp.ls_s3_wb >= 4 and afg_lsp_affpplp.ls_s3_wb < 5 then afg_pplp.vuid_population \
					end)),0) as ls_s3_wb_moderate, \
					coalesce(round(sum(case  \
					 when afg_lsp_affpplp.ls_s3_wb >= 2 and afg_lsp_affpplp.ls_s3_wb < 4 then afg_pplp.vuid_population \
					end)),0) as ls_s3_wb_low, \
					coalesce(round(sum(case \
					 when afg_lsp_affpplp.ls_s3_wb >= 1 and afg_lsp_affpplp.ls_s3_wb < 2 then afg_pplp.vuid_population \
					end)),0) as ls_s3_wb_very_low    \
					from afg_lsp_affpplp \
					inner join afg_pplp on afg_lsp_affpplp.vuid=afg_pplp.vuid \
					where ST_Intersects(afg_pplp.wkb_geometry,"+filterLock+")"
		else:
			sql = "select \
					coalesce(round(sum(case \
					 when afg_lsp_affpplp.lsi_immap >= 7 then afg_pplp.vuid_population \
					end)),0) as lsi_immap_very_high, \
					coalesce(round(sum(case \
					 when afg_lsp_affpplp.lsi_immap >= 5 and afg_lsp_affpplp.lsi_immap < 7 then afg_pplp.vuid_population \
					end)),0) as lsi_immap_high, \
					coalesce(round(sum(case \
					 when afg_lsp_affpplp.lsi_immap >= 4 and afg_lsp_affpplp.lsi_immap < 5 then afg_pplp.vuid_population \
					end)),0) as lsi_immap_moderate, \
					coalesce(round(sum(case \
					 when afg_lsp_affpplp.lsi_immap >= 2 and afg_lsp_affpplp.lsi_immap < 4 then afg_pplp.vuid_population \
					end)),0) as lsi_immap_low, \
					coalesce(round(sum(case \
					 when afg_lsp_affpplp.lsi_immap >= 1 and afg_lsp_affpplp.lsi_immap < 2 then afg_pplp.vuid_population \
					end)),0) as lsi_immap_very_low, \
					coalesce(round(sum(case \
					 when afg_lsp_affpplp.lsi_ku >= 7 then afg_pplp.vuid_population \
					end)),0) as lsi_ku_very_high, \
					coalesce(round(sum(case \
					 when afg_lsp_affpplp.lsi_ku >= 5 and afg_lsp_affpplp.lsi_ku < 7 then afg_pplp.vuid_population \
					end)),0) as lsi_ku_high, \
					coalesce(round(sum(case \
					 when afg_lsp_affpplp.lsi_ku >= 4 and afg_lsp_affpplp.lsi_ku < 5 then afg_pplp.vuid_population \
					end)),0) as lsi_ku_moderate, \
					coalesce(round(sum(case \
					 when afg_lsp_affpplp.lsi_ku >= 2 and afg_lsp_affpplp.lsi_ku < 4 then afg_pplp.vuid_population \
					end)),0) as lsi_ku_low, \
					coalesce(round(sum(case \
					 when afg_lsp_affpplp.lsi_ku >= 1 and afg_lsp_affpplp.lsi_ku < 2 then afg_pplp.vuid_population \
					end)),0) as lsi_ku_very_low, \
					coalesce(round(sum(case \
					 when afg_lsp_affpplp.ls_s1_wb >= 7 then afg_pplp.vuid_population \
					end)),0) as ls_s1_wb_very_high, \
					coalesce(round(sum(case \
					 when afg_lsp_affpplp.ls_s1_wb >= 5 and afg_lsp_affpplp.ls_s1_wb < 7 then afg_pplp.vuid_population \
					end)),0) as ls_s1_wb_high, \
					coalesce(round(sum(case \
					 when afg_lsp_affpplp.ls_s1_wb >= 4 and afg_lsp_affpplp.ls_s1_wb < 5 then afg_pplp.vuid_population \
					end)),0) as ls_s1_wb_moderate, \
					coalesce(round(sum(case  \
					 when afg_lsp_affpplp.ls_s1_wb >= 2 and afg_lsp_affpplp.ls_s1_wb < 4 then afg_pplp.vuid_population \
					end)),0) as ls_s1_wb_low, \
					coalesce(round(sum(case \
					 when afg_lsp_affpplp.ls_s1_wb >= 1 and afg_lsp_affpplp.ls_s1_wb < 2 then afg_pplp.vuid_population \
					end)),0) as ls_s1_wb_very_low, \
					coalesce(round(sum(case \
					 when afg_lsp_affpplp.ls_s2_wb >= 7 then afg_pplp.vuid_population \
					end)),0) as ls_s2_wb_very_high, \
					coalesce(round(sum(case \
					 when afg_lsp_affpplp.ls_s2_wb >= 5 and afg_lsp_affpplp.ls_s2_wb < 7 then afg_pplp.vuid_population \
					end)),0) as ls_s2_wb_high, \
					coalesce(round(sum(case \
					 when afg_lsp_affpplp.ls_s2_wb >= 4 and afg_lsp_affpplp.ls_s2_wb < 5 then afg_pplp.vuid_population \
					end)),0) as ls_s2_wb_moderate, \
					coalesce(round(sum(case \
					 when afg_lsp_affpplp.ls_s2_wb >= 2 and afg_lsp_affpplp.ls_s2_wb < 4 then afg_pplp.vuid_population \
					end)),0) as ls_s2_wb_low, \
					coalesce(round(sum(case \
					 when afg_lsp_affpplp.ls_s2_wb >= 1 and afg_lsp_affpplp.ls_s2_wb < 2 then afg_pplp.vuid_population \
					end)),0) as ls_s2_wb_very_low, \
					coalesce(round(sum(case \
					 when afg_lsp_affpplp.ls_s3_wb >= 7 then afg_pplp.vuid_population \
					end)),0) as ls_s3_wb_very_high, \
					coalesce(round(sum(case \
					 when afg_lsp_affpplp.ls_s3_wb >= 5 and afg_lsp_affpplp.ls_s3_wb < 7 then afg_pplp.vuid_population \
					end)),0) as ls_s3_wb_high, \
					coalesce(round(sum(case \
					 when afg_lsp_affpplp.ls_s3_wb >= 4 and afg_lsp_affpplp.ls_s3_wb < 5 then afg_pplp.vuid_population \
					end)),0) as ls_s3_wb_moderate, \
					coalesce(round(sum(case  \
					 when afg_lsp_affpplp.ls_s3_wb >= 2 and afg_lsp_affpplp.ls_s3_wb < 4 then afg_pplp.vuid_population \
					end)),0) as ls_s3_wb_low, \
					coalesce(round(sum(case \
					 when afg_lsp_affpplp.ls_s3_wb >= 1 and afg_lsp_affpplp.ls_s3_wb < 2 then afg_pplp.vuid_population \
					end)),0) as ls_s3_wb_very_low    \
					from afg_lsp_affpplp \
					inner join afg_pplp on afg_lsp_affpplp.vuid=afg_pplp.vuid \
					where ST_Intersects(afg_pplp.wkb_geometry,"+filterLock+")"

		cursor = connections['geodb'].cursor()
		row = query_to_dicts(cursor, sql)

		for i in row:
			for x in i:
				response.path('rawlandslide')[x] = i[x]

		for i in ['ls_s1_wb','ls_s2_wb','ls_s3_wb','lsi_immap','lsi_ku']:
			response[i] = {k:response['rawlandslide'].get('%s_%s'%(i,k)) or 0 for k in LANDSLIDE_TYPES}

		cursor.close()

	# if include_section('charts', includes, excludes):
	#     dataLC1 = []
	#     dataLC1.append(['',_('very high'), { 'role': 'annotation' }, { 'role': 'style' }, _('high'), { 'role': 'annotation' } , { 'role': 'style' }, _('moderate'), { 'role': 'annotation' }, { 'role': 'style' }, _('low'), { 'role': 'annotation' }, { 'role': 'style' }])
	#     dataLC1.append(['',  round(response['lsi_immap_very_high']), round(response['lsi_immap_very_high']), '#e31a1c', round(response['lsi_immap_high']), round(response['lsi_immap_high']), '#ff7f00', round(response['lsi_immap_moderate']), round(response['lsi_immap_moderate']), '#fff231', round(response['lsi_immap_low']), round(response['lsi_immap_low']), '#1eb263' ])
	#     # dataLC.append([_('Multi-criteria Landslide Susceptibility Index'),  round(response['lsi_ku_very_high']), round(response['lsi_ku_very_high']), round(response['lsi_ku_high']), round(response['lsi_ku_high']), round(response['lsi_ku_moderate']), round(response['lsi_ku_moderate']), round(response['lsi_ku_low']), round(response['lsi_ku_low']) ])
	#     # dataLC.append([_('Landslide susceptibility - bedrock landslides in slow evolution (S1)'),  round(response['ls_s1_wb_very_high']), round(response['ls_s1_wb_very_high']), round(response['ls_s1_wb_high']), round(response['ls_s1_wb_high']), round(response['ls_s1_wb_moderate']), round(response['ls_s1_wb_moderate']), round(response['ls_s1_wb_low']), round(response['ls_s1_wb_low']) ])
	#     # dataLC.append([_('Landslide susceptibility - bedrock landslides in rapid evolution (S2)'),  round(response['ls_s2_wb_very_high']), round(response['ls_s2_wb_very_high']), round(response['ls_s2_wb_high']), round(response['ls_s2_wb_high']), round(response['ls_s2_wb_moderate']), round(response['ls_s2_wb_moderate']), round(response['ls_s2_wb_low']), round(response['ls_s2_wb_low']) ])
	#     # dataLC.append([_('Landslide susceptibility - cover material in rapid evolution (S3)'),  round(response['ls_s3_wb_very_high']), round(response['ls_s3_wb_very_high']), round(response['ls_s3_wb_high']), round(response['ls_s3_wb_high']), round(response['ls_s3_wb_moderate']), round(response['ls_s3_wb_moderate']), round(response['ls_s3_wb_low']), round(response['ls_s3_wb_low']) ])
	#     response['landslide_chart1'] = gchart.BarChart(
	#         SimpleDataSource(data=dataLC1),
	#         html_id="pie_chart1",
	#         options={
	#             'title': _('# Population by Landslide Indexes (iMMAP 2017)'),
	#             'width': 300,
	#             'height': 300,
	#             'bars': 'horizontal',
	#             # 'axes': {
	#             #     'x': {
	#             #       '0': { 'side': 'top', 'label': _('Percentage')}
	#             #     },

	#             # },
	#             'bar': { 'groupWidth': '90%' },
	#             'chartArea': {'width': '100%'},
	#     })

	#     dataLC2 = []
	#     dataLC2.append(['',_('very high'), { 'role': 'annotation' }, { 'role': 'style' }, _('high'), { 'role': 'annotation' } , { 'role': 'style' }, _('moderate'), { 'role': 'annotation' }, { 'role': 'style' }, _('low'), { 'role': 'annotation' }, { 'role': 'style' }])
	#     dataLC2.append(['',  round(response['lsi_ku_very_high']), round(response['lsi_ku_very_high']), '#e31a1c', round(response['lsi_ku_high']), round(response['lsi_ku_high']), '#ff7f00', round(response['lsi_ku_moderate']), round(response['lsi_ku_moderate']), '#fff231', round(response['lsi_ku_low']), round(response['lsi_ku_low']), '#1eb263' ])
	#     response['landslide_chart2'] = gchart.BarChart(
	#         SimpleDataSource(data=dataLC2),
	#         html_id="pie_chart2",
	#         options={
	#             'title': _('# Population by Multi-criteria Landslide Susceptibility Index'),
	#             'width': 300,
	#             'height': 300,
	#             'bars': 'horizontal',
	#             # 'axes': {
	#             #     'x': {
	#             #       '0': { 'side': 'top', 'label': _('Percentage')}
	#             #     },

	#             # },
	#             'bar': { 'groupWidth': '90%' },
	#             'chartArea': {'width': '100%'},
	#     })

	#     dataLC3 = []
	#     dataLC3.append(['',_('very high'), { 'role': 'annotation' }, { 'role': 'style' }, _('high'), { 'role': 'annotation' } , { 'role': 'style' }, _('moderate'), { 'role': 'annotation' }, { 'role': 'style' }, _('low'), { 'role': 'annotation' }, { 'role': 'style' }])
	#     dataLC3.append(['',  round(response['ls_s1_wb_very_high']), round(response['ls_s1_wb_very_high']), '#e31a1c', round(response['ls_s1_wb_high']), round(response['ls_s1_wb_high']), '#ff7f00', round(response['ls_s1_wb_moderate']), round(response['ls_s1_wb_moderate']), '#fff231', round(response['ls_s1_wb_low']), round(response['ls_s1_wb_low']), '#1eb263' ])
	#     response['landslide_chart3'] = gchart.BarChart(
	#         SimpleDataSource(data=dataLC3),
	#         html_id="pie_chart3",
	#         options={
	#             'title': _('# Population by Landslide susceptibility - bedrock landslides in slow evolution (S1)'),
	#             'width': 300,
	#             'height': 300,
	#             'bars': 'horizontal',
	#             # 'axes': {
	#             #     'x': {
	#             #       '0': { 'side': 'top', 'label': _('Percentage')}
	#             #     },

	#             # },
	#             'bar': { 'groupWidth': '90%' },
	#             'chartArea': {'width': '100%'},
	#     })

	#     dataLC4 = []
	#     dataLC4.append(['',_('very high'), { 'role': 'annotation' }, { 'role': 'style' }, _('high'), { 'role': 'annotation' } , { 'role': 'style' }, _('moderate'), { 'role': 'annotation' }, { 'role': 'style' }, _('low'), { 'role': 'annotation' }, { 'role': 'style' }])
	#     dataLC4.append(['',  round(response['ls_s2_wb_very_high']), round(response['ls_s2_wb_very_high']), '#e31a1c', round(response['ls_s2_wb_high']), round(response['ls_s2_wb_high']), '#ff7f00', round(response['ls_s2_wb_moderate']), round(response['ls_s2_wb_moderate']), '#fff231', round(response['ls_s2_wb_low']), round(response['ls_s2_wb_low']), '#1eb263' ])
	#     response['landslide_chart4'] = gchart.BarChart(
	#         SimpleDataSource(data=dataLC4),
	#         html_id="pie_chart4",
	#         options={
	#             'title': _('# Population by Landslide susceptibility - bedrock landslides in rapid evolution (S2)'),
	#             'width': 300,
	#             'height': 300,
	#             'bars': 'horizontal',
	#             # 'axes': {
	#             #     'x': {
	#             #       '0': { 'side': 'top', 'label': _('Percentage')}
	#             #     },

	#             # },
	#             'bar': { 'groupWidth': '90%' },
	#             'chartArea': {'width': '100%'},
	#     })

	#     dataLC5 = []
	#     dataLC5.append(['',_('very high'), { 'role': 'annotation' }, { 'role': 'style' }, _('high'), { 'role': 'annotation' } , { 'role': 'style' }, _('moderate'), { 'role': 'annotation' }, { 'role': 'style' }, _('low'), { 'role': 'annotation' }, { 'role': 'style' }])
	#     dataLC5.append(['',  round(response['ls_s3_wb_very_high']), round(response['ls_s3_wb_very_high']), '#e31a1c', round(response['ls_s3_wb_high']), round(response['ls_s3_wb_high']), '#ff7f00', round(response['ls_s3_wb_moderate']), round(response['ls_s3_wb_moderate']), '#fff231', round(response['ls_s3_wb_low']), round(response['ls_s3_wb_low']), '#1eb263' ])
	#     response['landslide_chart5'] = gchart.BarChart(
	#         SimpleDataSource(data=dataLC5),
	#         html_id="pie_chart5",
	#         options={
	#             'title': _('# Population by Landslide susceptibility - bedrock landslides in rapid evolution (S2)'),
	#             'width': 300,
	#             'height': 300,
	#             'bars': 'horizontal',
	#             # 'axes': {
	#             #     'x': {
	#             #       '0': { 'side': 'top', 'label': _('Percentage')}
	#             #     },

	#             # },
	#             'bar': { 'groupWidth': '90%' },
	#             'chartArea': {'width': '100%'},
	#     })

	if include_section('GeoJson', includes, excludes):
		response['GeoJson'] = getGeoJson(request, flag, code)

	return response

# moved from geodb.geoapi

class getLandslide(ModelResource):
	class Meta:
		resource_name = 'statistic_landslide'
		allowed_methods = ['post']
		detail_allowed_methods = ['post']
		cache = SimpleCache() 
		object_class=None

	def post_list(self, request, **kwargs):
		self.method_check(request, allowed=['post'])
		response = self.getData(request)
		return self.create_response(request, response)   

	def getData(self, request):

		p = urlparse(request.META.get('HTTP_REFERER')).path.split('/')
		mapCode = p[3] if 'v2' in p else p[2]
		map_obj = _resolve_map(request, mapCode, 'base.view_resourcebase', _PERMISSION_MSG_VIEW)

		queryset = matrix(user=request.user,resourceid=map_obj,action='Interactive Calculation')
		queryset.save()

		boundaryFilter = json.loads(request.body)

		wkts = ['ST_GeomFromText(\'%s\',4326)'%(i) for i in boundaryFilter.get('spatialfilter')]
		bring = wkts[-1] if len(wkts) else None
		filterLock = 'ST_Union(ARRAY[%s])'%(','.join(wkts))
		boundaryFilter = json.loads(request.body)

		response = getLandslideStatistic(request, filterLock, boundaryFilter.get('flag'), boundaryFilter.get('code'))

		return response

		# temp1 = []
		# for i in boundaryFilter['spatialfilter']:
		# 	temp1.append('ST_GeomFromText(\''+i+'\',4326)')

		# temp2 = 'ARRAY['
		# first=True
		# for i in temp1:
		# 	if first:
		# 		 temp2 = temp2 + i
		# 		 first=False
		# 	else :
		# 		 temp2 = temp2 + ', ' + i  

		# temp2 = temp2+']'
		
		# filterLock = 'ST_Union('+temp2+')'
		# flag = boundaryFilter['flag']
		# code = boundaryFilter['code']

		# response = {}

		# if flag=='entireAfg':
		# 	sql = "select \
		# 			coalesce(round(sum(case \
		# 			 when afg_lsp_affpplp.lsi_immap >= 7 then afg_pplp.vuid_population \
		# 			end)),0) as lsi_immap_very_high, \
		# 			coalesce(round(sum(case \
		# 			 when afg_lsp_affpplp.lsi_immap >= 5 and afg_lsp_affpplp.lsi_immap < 7 then afg_pplp.vuid_population \
		# 			end)),0) as lsi_immap_high, \
		# 			coalesce(round(sum(case \
		# 			 when afg_lsp_affpplp.lsi_immap >= 4 and afg_lsp_affpplp.lsi_immap < 5 then afg_pplp.vuid_population \
		# 			end)),0) as lsi_immap_moderate, \
		# 			coalesce(round(sum(case \
		# 			 when afg_lsp_affpplp.lsi_immap >= 2 and afg_lsp_affpplp.lsi_immap < 4 then afg_pplp.vuid_population \
		# 			end)),0) as lsi_immap_low, \
		# 			coalesce(round(sum(case \
		# 			 when afg_lsp_affpplp.lsi_immap >= 1 and afg_lsp_affpplp.lsi_immap < 2 then afg_pplp.vuid_population \
		# 			end)),0) as lsi_immap_very_low, \
		# 			coalesce(round(sum(case \
		# 			 when afg_lsp_affpplp.lsi_ku >= 7 then afg_pplp.vuid_population \
		# 			end)),0) as lsi_ku_very_high, \
		# 			coalesce(round(sum(case \
		# 			 when afg_lsp_affpplp.lsi_ku >= 5 and afg_lsp_affpplp.lsi_ku < 7 then afg_pplp.vuid_population \
		# 			end)),0) as lsi_ku_high, \
		# 			coalesce(round(sum(case \
		# 			 when afg_lsp_affpplp.lsi_ku >= 4 and afg_lsp_affpplp.lsi_ku < 5 then afg_pplp.vuid_population \
		# 			end)),0) as lsi_ku_moderate, \
		# 			coalesce(round(sum(case \
		# 			 when afg_lsp_affpplp.lsi_ku >= 2 and afg_lsp_affpplp.lsi_ku < 4 then afg_pplp.vuid_population \
		# 			end)),0) as lsi_ku_low, \
		# 			coalesce(round(sum(case \
		# 			 when afg_lsp_affpplp.lsi_ku >= 1 and afg_lsp_affpplp.lsi_ku < 2 then afg_pplp.vuid_population \
		# 			end)),0) as lsi_ku_very_low, \
		# 			coalesce(round(sum(case \
		# 			 when afg_lsp_affpplp.ls_s1_wb >= 7 then afg_pplp.vuid_population \
		# 			end)),0) as ls_s1_wb_very_high, \
		# 			coalesce(round(sum(case \
		# 			 when afg_lsp_affpplp.ls_s1_wb >= 5 and afg_lsp_affpplp.ls_s1_wb < 7 then afg_pplp.vuid_population \
		# 			end)),0) as ls_s1_wb_high, \
		# 			coalesce(round(sum(case \
		# 			 when afg_lsp_affpplp.ls_s1_wb >= 4 and afg_lsp_affpplp.ls_s1_wb < 5 then afg_pplp.vuid_population \
		# 			end)),0) as ls_s1_wb_moderate, \
		# 			coalesce(round(sum(case  \
		# 			 when afg_lsp_affpplp.ls_s1_wb >= 2 and afg_lsp_affpplp.ls_s1_wb < 4 then afg_pplp.vuid_population \
		# 			end)),0) as ls_s1_wb_low, \
		# 			coalesce(round(sum(case \
		# 			 when afg_lsp_affpplp.ls_s1_wb >= 1 and afg_lsp_affpplp.ls_s1_wb < 2 then afg_pplp.vuid_population \
		# 			end)),0) as ls_s1_wb_very_low, \
		# 			coalesce(round(sum(case \
		# 			 when afg_lsp_affpplp.ls_s2_wb >= 7 then afg_pplp.vuid_population \
		# 			end)),0) as ls_s2_wb_very_high, \
		# 			coalesce(round(sum(case \
		# 			 when afg_lsp_affpplp.ls_s2_wb >= 5 and afg_lsp_affpplp.ls_s2_wb < 7 then afg_pplp.vuid_population \
		# 			end)),0) as ls_s2_wb_high, \
		# 			coalesce(round(sum(case \
		# 			 when afg_lsp_affpplp.ls_s2_wb >= 4 and afg_lsp_affpplp.ls_s2_wb < 5 then afg_pplp.vuid_population \
		# 			end)),0) as ls_s2_wb_moderate, \
		# 			coalesce(round(sum(case \
		# 			 when afg_lsp_affpplp.ls_s2_wb >= 2 and afg_lsp_affpplp.ls_s2_wb < 4 then afg_pplp.vuid_population \
		# 			end)),0) as ls_s2_wb_low, \
		# 			coalesce(round(sum(case \
		# 			 when afg_lsp_affpplp.ls_s2_wb >= 1 and afg_lsp_affpplp.ls_s2_wb < 2 then afg_pplp.vuid_population \
		# 			end)),0) as ls_s2_wb_very_low, \
		# 			coalesce(round(sum(case \
		# 			 when afg_lsp_affpplp.ls_s3_wb >= 7 then afg_pplp.vuid_population \
		# 			end)),0) as ls_s3_wb_very_high, \
		# 			coalesce(round(sum(case \
		# 			 when afg_lsp_affpplp.ls_s3_wb >= 5 and afg_lsp_affpplp.ls_s3_wb < 7 then afg_pplp.vuid_population \
		# 			end)),0) as ls_s3_wb_high, \
		# 			coalesce(round(sum(case \
		# 			 when afg_lsp_affpplp.ls_s3_wb >= 4 and afg_lsp_affpplp.ls_s3_wb < 5 then afg_pplp.vuid_population \
		# 			end)),0) as ls_s3_wb_moderate, \
		# 			coalesce(round(sum(case  \
		# 			 when afg_lsp_affpplp.ls_s3_wb >= 2 and afg_lsp_affpplp.ls_s3_wb < 4 then afg_pplp.vuid_population \
		# 			end)),0) as ls_s3_wb_low, \
		# 			coalesce(round(sum(case \
		# 			 when afg_lsp_affpplp.ls_s3_wb >= 1 and afg_lsp_affpplp.ls_s3_wb < 2 then afg_pplp.vuid_population \
		# 			end)),0) as ls_s3_wb_very_low    \
		# 			from afg_lsp_affpplp \
		# 			inner join afg_pplp on afg_lsp_affpplp.vuid=afg_pplp.vuid"

		# elif flag =='currentProvince':
		# 	if len(str(boundaryFilter['code'])) > 2:
		# 		ff0001 =  "afg_pplp.dist_code  = '"+str(boundaryFilter['code'])+"'"
		# 	else :
		# 		ff0001 =  "afg_pplp.prov_code_1  = '"+str(boundaryFilter['code'])+"'" 

		# 	sql = "select \
		# 			coalesce(round(sum(case \
		# 			 when afg_lsp_affpplp.lsi_immap >= 7 then afg_pplp.vuid_population \
		# 			end)),0) as lsi_immap_very_high, \
		# 			coalesce(round(sum(case \
		# 			 when afg_lsp_affpplp.lsi_immap >= 5 and afg_lsp_affpplp.lsi_immap < 7 then afg_pplp.vuid_population \
		# 			end)),0) as lsi_immap_high, \
		# 			coalesce(round(sum(case \
		# 			 when afg_lsp_affpplp.lsi_immap >= 4 and afg_lsp_affpplp.lsi_immap < 5 then afg_pplp.vuid_population \
		# 			end)),0) as lsi_immap_moderate, \
		# 			coalesce(round(sum(case \
		# 			 when afg_lsp_affpplp.lsi_immap >= 2 and afg_lsp_affpplp.lsi_immap < 4 then afg_pplp.vuid_population \
		# 			end)),0) as lsi_immap_low, \
		# 			coalesce(round(sum(case \
		# 			 when afg_lsp_affpplp.lsi_immap >= 1 and afg_lsp_affpplp.lsi_immap < 2 then afg_pplp.vuid_population \
		# 			end)),0) as lsi_immap_very_low, \
		# 			coalesce(round(sum(case \
		# 			 when afg_lsp_affpplp.lsi_ku >= 7 then afg_pplp.vuid_population \
		# 			end)),0) as lsi_ku_very_high, \
		# 			coalesce(round(sum(case \
		# 			 when afg_lsp_affpplp.lsi_ku >= 5 and afg_lsp_affpplp.lsi_ku < 7 then afg_pplp.vuid_population \
		# 			end)),0) as lsi_ku_high, \
		# 			coalesce(round(sum(case \
		# 			 when afg_lsp_affpplp.lsi_ku >= 4 and afg_lsp_affpplp.lsi_ku < 5 then afg_pplp.vuid_population \
		# 			end)),0) as lsi_ku_moderate, \
		# 			coalesce(round(sum(case \
		# 			 when afg_lsp_affpplp.lsi_ku >= 2 and afg_lsp_affpplp.lsi_ku < 4 then afg_pplp.vuid_population \
		# 			end)),0) as lsi_ku_low, \
		# 			coalesce(round(sum(case \
		# 			 when afg_lsp_affpplp.lsi_ku >= 1 and afg_lsp_affpplp.lsi_ku < 2 then afg_pplp.vuid_population \
		# 			end)),0) as lsi_ku_very_low, \
		# 			coalesce(round(sum(case \
		# 			 when afg_lsp_affpplp.ls_s1_wb >= 7 then afg_pplp.vuid_population \
		# 			end)),0) as ls_s1_wb_very_high, \
		# 			coalesce(round(sum(case \
		# 			 when afg_lsp_affpplp.ls_s1_wb >= 5 and afg_lsp_affpplp.ls_s1_wb < 7 then afg_pplp.vuid_population \
		# 			end)),0) as ls_s1_wb_high, \
		# 			coalesce(round(sum(case \
		# 			 when afg_lsp_affpplp.ls_s1_wb >= 4 and afg_lsp_affpplp.ls_s1_wb < 5 then afg_pplp.vuid_population \
		# 			end)),0) as ls_s1_wb_moderate, \
		# 			coalesce(round(sum(case  \
		# 			 when afg_lsp_affpplp.ls_s1_wb >= 2 and afg_lsp_affpplp.ls_s1_wb < 4 then afg_pplp.vuid_population \
		# 			end)),0) as ls_s1_wb_low, \
		# 			coalesce(round(sum(case \
		# 			 when afg_lsp_affpplp.ls_s1_wb >= 1 and afg_lsp_affpplp.ls_s1_wb < 2 then afg_pplp.vuid_population \
		# 			end)),0) as ls_s1_wb_very_low, \
		# 			coalesce(round(sum(case \
		# 			 when afg_lsp_affpplp.ls_s2_wb >= 7 then afg_pplp.vuid_population \
		# 			end)),0) as ls_s2_wb_very_high, \
		# 			coalesce(round(sum(case \
		# 			 when afg_lsp_affpplp.ls_s2_wb >= 5 and afg_lsp_affpplp.ls_s2_wb < 7 then afg_pplp.vuid_population \
		# 			end)),0) as ls_s2_wb_high, \
		# 			coalesce(round(sum(case \
		# 			 when afg_lsp_affpplp.ls_s2_wb >= 4 and afg_lsp_affpplp.ls_s2_wb < 5 then afg_pplp.vuid_population \
		# 			end)),0) as ls_s2_wb_moderate, \
		# 			coalesce(round(sum(case \
		# 			 when afg_lsp_affpplp.ls_s2_wb >= 2 and afg_lsp_affpplp.ls_s2_wb < 4 then afg_pplp.vuid_population \
		# 			end)),0) as ls_s2_wb_low, \
		# 			coalesce(round(sum(case \
		# 			 when afg_lsp_affpplp.ls_s2_wb >= 1 and afg_lsp_affpplp.ls_s2_wb < 2 then afg_pplp.vuid_population \
		# 			end)),0) as ls_s2_wb_very_low, \
		# 			coalesce(round(sum(case \
		# 			 when afg_lsp_affpplp.ls_s3_wb >= 7 then afg_pplp.vuid_population \
		# 			end)),0) as ls_s3_wb_very_high, \
		# 			coalesce(round(sum(case \
		# 			 when afg_lsp_affpplp.ls_s3_wb >= 5 and afg_lsp_affpplp.ls_s3_wb < 7 then afg_pplp.vuid_population \
		# 			end)),0) as ls_s3_wb_high, \
		# 			coalesce(round(sum(case \
		# 			 when afg_lsp_affpplp.ls_s3_wb >= 4 and afg_lsp_affpplp.ls_s3_wb < 5 then afg_pplp.vuid_population \
		# 			end)),0) as ls_s3_wb_moderate, \
		# 			coalesce(round(sum(case  \
		# 			 when afg_lsp_affpplp.ls_s3_wb >= 2 and afg_lsp_affpplp.ls_s3_wb < 4 then afg_pplp.vuid_population \
		# 			end)),0) as ls_s3_wb_low, \
		# 			coalesce(round(sum(case \
		# 			 when afg_lsp_affpplp.ls_s3_wb >= 1 and afg_lsp_affpplp.ls_s3_wb < 2 then afg_pplp.vuid_population \
		# 			end)),0) as ls_s3_wb_very_low    \
		# 			from afg_lsp_affpplp \
		# 			inner join afg_pplp on afg_lsp_affpplp.vuid=afg_pplp.vuid \
		# 			where " +  ff0001  

		# elif flag =='drawArea':
		# 	sql = "select \
		# 			coalesce(round(sum(case \
		# 			 when afg_lsp_affpplp.lsi_immap >= 7 then afg_pplp.vuid_population \
		# 			end)),0) as lsi_immap_very_high, \
		# 			coalesce(round(sum(case \
		# 			 when afg_lsp_affpplp.lsi_immap >= 5 and afg_lsp_affpplp.lsi_immap < 7 then afg_pplp.vuid_population \
		# 			end)),0) as lsi_immap_high, \
		# 			coalesce(round(sum(case \
		# 			 when afg_lsp_affpplp.lsi_immap >= 4 and afg_lsp_affpplp.lsi_immap < 5 then afg_pplp.vuid_population \
		# 			end)),0) as lsi_immap_moderate, \
		# 			coalesce(round(sum(case \
		# 			 when afg_lsp_affpplp.lsi_immap >= 2 and afg_lsp_affpplp.lsi_immap < 4 then afg_pplp.vuid_population \
		# 			end)),0) as lsi_immap_low, \
		# 			coalesce(round(sum(case \
		# 			 when afg_lsp_affpplp.lsi_immap >= 1 and afg_lsp_affpplp.lsi_immap < 2 then afg_pplp.vuid_population \
		# 			end)),0) as lsi_immap_very_low, \
		# 			coalesce(round(sum(case \
		# 			 when afg_lsp_affpplp.lsi_ku >= 7 then afg_pplp.vuid_population \
		# 			end)),0) as lsi_ku_very_high, \
		# 			coalesce(round(sum(case \
		# 			 when afg_lsp_affpplp.lsi_ku >= 5 and afg_lsp_affpplp.lsi_ku < 7 then afg_pplp.vuid_population \
		# 			end)),0) as lsi_ku_high, \
		# 			coalesce(round(sum(case \
		# 			 when afg_lsp_affpplp.lsi_ku >= 4 and afg_lsp_affpplp.lsi_ku < 5 then afg_pplp.vuid_population \
		# 			end)),0) as lsi_ku_moderate, \
		# 			coalesce(round(sum(case \
		# 			 when afg_lsp_affpplp.lsi_ku >= 2 and afg_lsp_affpplp.lsi_ku < 4 then afg_pplp.vuid_population \
		# 			end)),0) as lsi_ku_low, \
		# 			coalesce(round(sum(case \
		# 			 when afg_lsp_affpplp.lsi_ku >= 1 and afg_lsp_affpplp.lsi_ku < 2 then afg_pplp.vuid_population \
		# 			end)),0) as lsi_ku_very_low, \
		# 			coalesce(round(sum(case \
		# 			 when afg_lsp_affpplp.ls_s1_wb >= 7 then afg_pplp.vuid_population \
		# 			end)),0) as ls_s1_wb_very_high, \
		# 			coalesce(round(sum(case \
		# 			 when afg_lsp_affpplp.ls_s1_wb >= 5 and afg_lsp_affpplp.ls_s1_wb < 7 then afg_pplp.vuid_population \
		# 			end)),0) as ls_s1_wb_high, \
		# 			coalesce(round(sum(case \
		# 			 when afg_lsp_affpplp.ls_s1_wb >= 4 and afg_lsp_affpplp.ls_s1_wb < 5 then afg_pplp.vuid_population \
		# 			end)),0) as ls_s1_wb_moderate, \
		# 			coalesce(round(sum(case  \
		# 			 when afg_lsp_affpplp.ls_s1_wb >= 2 and afg_lsp_affpplp.ls_s1_wb < 4 then afg_pplp.vuid_population \
		# 			end)),0) as ls_s1_wb_low, \
		# 			coalesce(round(sum(case \
		# 			 when afg_lsp_affpplp.ls_s1_wb >= 1 and afg_lsp_affpplp.ls_s1_wb < 2 then afg_pplp.vuid_population \
		# 			end)),0) as ls_s1_wb_very_low, \
		# 			coalesce(round(sum(case \
		# 			 when afg_lsp_affpplp.ls_s2_wb >= 7 then afg_pplp.vuid_population \
		# 			end)),0) as ls_s2_wb_very_high, \
		# 			coalesce(round(sum(case \
		# 			 when afg_lsp_affpplp.ls_s2_wb >= 5 and afg_lsp_affpplp.ls_s2_wb < 7 then afg_pplp.vuid_population \
		# 			end)),0) as ls_s2_wb_high, \
		# 			coalesce(round(sum(case \
		# 			 when afg_lsp_affpplp.ls_s2_wb >= 4 and afg_lsp_affpplp.ls_s2_wb < 5 then afg_pplp.vuid_population \
		# 			end)),0) as ls_s2_wb_moderate, \
		# 			coalesce(round(sum(case \
		# 			 when afg_lsp_affpplp.ls_s2_wb >= 2 and afg_lsp_affpplp.ls_s2_wb < 4 then afg_pplp.vuid_population \
		# 			end)),0) as ls_s2_wb_low, \
		# 			coalesce(round(sum(case \
		# 			 when afg_lsp_affpplp.ls_s2_wb >= 1 and afg_lsp_affpplp.ls_s2_wb < 2 then afg_pplp.vuid_population \
		# 			end)),0) as ls_s2_wb_very_low, \
		# 			coalesce(round(sum(case \
		# 			 when afg_lsp_affpplp.ls_s3_wb >= 7 then afg_pplp.vuid_population \
		# 			end)),0) as ls_s3_wb_very_high, \
		# 			coalesce(round(sum(case \
		# 			 when afg_lsp_affpplp.ls_s3_wb >= 5 and afg_lsp_affpplp.ls_s3_wb < 7 then afg_pplp.vuid_population \
		# 			end)),0) as ls_s3_wb_high, \
		# 			coalesce(round(sum(case \
		# 			 when afg_lsp_affpplp.ls_s3_wb >= 4 and afg_lsp_affpplp.ls_s3_wb < 5 then afg_pplp.vuid_population \
		# 			end)),0) as ls_s3_wb_moderate, \
		# 			coalesce(round(sum(case  \
		# 			 when afg_lsp_affpplp.ls_s3_wb >= 2 and afg_lsp_affpplp.ls_s3_wb < 4 then afg_pplp.vuid_population \
		# 			end)),0) as ls_s3_wb_low, \
		# 			coalesce(round(sum(case \
		# 			 when afg_lsp_affpplp.ls_s3_wb >= 1 and afg_lsp_affpplp.ls_s3_wb < 2 then afg_pplp.vuid_population \
		# 			end)),0) as ls_s3_wb_very_low    \
		# 			from afg_lsp_affpplp \
		# 			inner join afg_pplp on afg_lsp_affpplp.vuid=afg_pplp.vuid \
		# 			where ST_Intersects(afg_pplp.wkb_geometry,"+filterLock+")"
		# else:
		# 	sql = "select \
		# 			coalesce(round(sum(case \
		# 			 when afg_lsp_affpplp.lsi_immap >= 7 then afg_pplp.vuid_population \
		# 			end)),0) as lsi_immap_very_high, \
		# 			coalesce(round(sum(case \
		# 			 when afg_lsp_affpplp.lsi_immap >= 5 and afg_lsp_affpplp.lsi_immap < 7 then afg_pplp.vuid_population \
		# 			end)),0) as lsi_immap_high, \
		# 			coalesce(round(sum(case \
		# 			 when afg_lsp_affpplp.lsi_immap >= 4 and afg_lsp_affpplp.lsi_immap < 5 then afg_pplp.vuid_population \
		# 			end)),0) as lsi_immap_moderate, \
		# 			coalesce(round(sum(case \
		# 			 when afg_lsp_affpplp.lsi_immap >= 2 and afg_lsp_affpplp.lsi_immap < 4 then afg_pplp.vuid_population \
		# 			end)),0) as lsi_immap_low, \
		# 			coalesce(round(sum(case \
		# 			 when afg_lsp_affpplp.lsi_immap >= 1 and afg_lsp_affpplp.lsi_immap < 2 then afg_pplp.vuid_population \
		# 			end)),0) as lsi_immap_very_low, \
		# 			coalesce(round(sum(case \
		# 			 when afg_lsp_affpplp.lsi_ku >= 7 then afg_pplp.vuid_population \
		# 			end)),0) as lsi_ku_very_high, \
		# 			coalesce(round(sum(case \
		# 			 when afg_lsp_affpplp.lsi_ku >= 5 and afg_lsp_affpplp.lsi_ku < 7 then afg_pplp.vuid_population \
		# 			end)),0) as lsi_ku_high, \
		# 			coalesce(round(sum(case \
		# 			 when afg_lsp_affpplp.lsi_ku >= 4 and afg_lsp_affpplp.lsi_ku < 5 then afg_pplp.vuid_population \
		# 			end)),0) as lsi_ku_moderate, \
		# 			coalesce(round(sum(case \
		# 			 when afg_lsp_affpplp.lsi_ku >= 2 and afg_lsp_affpplp.lsi_ku < 4 then afg_pplp.vuid_population \
		# 			end)),0) as lsi_ku_low, \
		# 			coalesce(round(sum(case \
		# 			 when afg_lsp_affpplp.lsi_ku >= 1 and afg_lsp_affpplp.lsi_ku < 2 then afg_pplp.vuid_population \
		# 			end)),0) as lsi_ku_very_low, \
		# 			coalesce(round(sum(case \
		# 			 when afg_lsp_affpplp.ls_s1_wb >= 7 then afg_pplp.vuid_population \
		# 			end)),0) as ls_s1_wb_very_high, \
		# 			coalesce(round(sum(case \
		# 			 when afg_lsp_affpplp.ls_s1_wb >= 5 and afg_lsp_affpplp.ls_s1_wb < 7 then afg_pplp.vuid_population \
		# 			end)),0) as ls_s1_wb_high, \
		# 			coalesce(round(sum(case \
		# 			 when afg_lsp_affpplp.ls_s1_wb >= 4 and afg_lsp_affpplp.ls_s1_wb < 5 then afg_pplp.vuid_population \
		# 			end)),0) as ls_s1_wb_moderate, \
		# 			coalesce(round(sum(case  \
		# 			 when afg_lsp_affpplp.ls_s1_wb >= 2 and afg_lsp_affpplp.ls_s1_wb < 4 then afg_pplp.vuid_population \
		# 			end)),0) as ls_s1_wb_low, \
		# 			coalesce(round(sum(case \
		# 			 when afg_lsp_affpplp.ls_s1_wb >= 1 and afg_lsp_affpplp.ls_s1_wb < 2 then afg_pplp.vuid_population \
		# 			end)),0) as ls_s1_wb_very_low, \
		# 			coalesce(round(sum(case \
		# 			 when afg_lsp_affpplp.ls_s2_wb >= 7 then afg_pplp.vuid_population \
		# 			end)),0) as ls_s2_wb_very_high, \
		# 			coalesce(round(sum(case \
		# 			 when afg_lsp_affpplp.ls_s2_wb >= 5 and afg_lsp_affpplp.ls_s2_wb < 7 then afg_pplp.vuid_population \
		# 			end)),0) as ls_s2_wb_high, \
		# 			coalesce(round(sum(case \
		# 			 when afg_lsp_affpplp.ls_s2_wb >= 4 and afg_lsp_affpplp.ls_s2_wb < 5 then afg_pplp.vuid_population \
		# 			end)),0) as ls_s2_wb_moderate, \
		# 			coalesce(round(sum(case \
		# 			 when afg_lsp_affpplp.ls_s2_wb >= 2 and afg_lsp_affpplp.ls_s2_wb < 4 then afg_pplp.vuid_population \
		# 			end)),0) as ls_s2_wb_low, \
		# 			coalesce(round(sum(case \
		# 			 when afg_lsp_affpplp.ls_s2_wb >= 1 and afg_lsp_affpplp.ls_s2_wb < 2 then afg_pplp.vuid_population \
		# 			end)),0) as ls_s2_wb_very_low, \
		# 			coalesce(round(sum(case \
		# 			 when afg_lsp_affpplp.ls_s3_wb >= 7 then afg_pplp.vuid_population \
		# 			end)),0) as ls_s3_wb_very_high, \
		# 			coalesce(round(sum(case \
		# 			 when afg_lsp_affpplp.ls_s3_wb >= 5 and afg_lsp_affpplp.ls_s3_wb < 7 then afg_pplp.vuid_population \
		# 			end)),0) as ls_s3_wb_high, \
		# 			coalesce(round(sum(case \
		# 			 when afg_lsp_affpplp.ls_s3_wb >= 4 and afg_lsp_affpplp.ls_s3_wb < 5 then afg_pplp.vuid_population \
		# 			end)),0) as ls_s3_wb_moderate, \
		# 			coalesce(round(sum(case  \
		# 			 when afg_lsp_affpplp.ls_s3_wb >= 2 and afg_lsp_affpplp.ls_s3_wb < 4 then afg_pplp.vuid_population \
		# 			end)),0) as ls_s3_wb_low, \
		# 			coalesce(round(sum(case \
		# 			 when afg_lsp_affpplp.ls_s3_wb >= 1 and afg_lsp_affpplp.ls_s3_wb < 2 then afg_pplp.vuid_population \
		# 			end)),0) as ls_s3_wb_very_low    \
		# 			from afg_lsp_affpplp \
		# 			inner join afg_pplp on afg_lsp_affpplp.vuid=afg_pplp.vuid \
		# 			where ST_Intersects(afg_pplp.wkb_geometry,"+filterLock+")"
		
		# cursor = connections['geodb'].cursor()
		# row = query_to_dicts(cursor, sql)
		# counts = []
		# for i in row:
		# 	counts.append(i)
		# cursor.close()

		# return counts[0]

# moved from geodb.views

def getLandSlideInfoVillages(request):
	template = './landslideinfo.html'
	village = request.GET["v"]
	currentdate = datetime.datetime.utcnow()
	year = currentdate.strftime("%Y")
	month = currentdate.strftime("%m")
	day = currentdate.strftime("%d")

	context_dict = getCommonVillageData(village)

	px = get_object_or_404(AfgLspAffpplp, vuid=village)
	try:
		context_dict['landslide_risk'] = px.lsi_immap
	except:
		context_dict['landslide_risk'] = 0

	try:
		context_dict['landslide_risk_lsi_ku'] = px.lsi_ku
	except:
		context_dict['landslide_risk_lsi_ku'] = 0

	try:
		context_dict['landslide_risk_ls_s1_wb'] = px.ls_s1_wb
	except:
		context_dict['landslide_risk_ls_s1_wb'] = 0

	try:
		context_dict['landslide_risk_ls_s2_wb'] = px.ls_s2_wb
	except:
		context_dict['landslide_risk_ls_s2_wb'] = 0

	try:
		context_dict['landslide_risk_ls_s3_wb'] = px.ls_s3_wb
	except:
		context_dict['landslide_risk_ls_s3_wb'] = 0

	if context_dict['landslide_risk'] >= 7:
		context_dict['landslide_risk'] = 'Very High'
	elif context_dict['landslide_risk'] >= 5 and context_dict['landslide_risk'] < 7:
		context_dict['landslide_risk'] = 'High'
	elif context_dict['landslide_risk'] >= 4 and context_dict['landslide_risk'] < 5:
		context_dict['landslide_risk'] = 'Moderate'
	elif context_dict['landslide_risk'] >= 2 and context_dict['landslide_risk'] < 4:
		context_dict['landslide_risk'] = 'Low'
	elif context_dict['landslide_risk'] >= 1 and context_dict['landslide_risk'] < 2:
		context_dict['landslide_risk'] = 'Very Low'
	else :
		context_dict['landslide_risk'] = 'None'


	if context_dict['landslide_risk_lsi_ku'] >= 7:
		context_dict['landslide_risk_lsi_ku'] = 'Very High'
	elif context_dict['landslide_risk_lsi_ku'] >= 5 and context_dict['landslide_risk_lsi_ku'] < 7:
		context_dict['landslide_risk_lsi_ku'] = 'High'
	elif context_dict['landslide_risk_lsi_ku'] >= 4 and context_dict['landslide_risk_lsi_ku'] < 5:
		context_dict['landslide_risk_lsi_ku'] = 'Moderate'
	elif context_dict['landslide_risk_lsi_ku'] >= 2 and context_dict['landslide_risk_lsi_ku'] < 4:
		context_dict['landslide_risk_lsi_ku'] = 'Low'
	elif context_dict['landslide_risk_lsi_ku'] >= 1 and context_dict['landslide_risk_lsi_ku'] < 2:
		context_dict['landslide_risk_lsi_ku'] = 'Very Low'
	else :
		context_dict['landslide_risk_lsi_ku'] = 'None'

	if context_dict['landslide_risk_ls_s1_wb'] >= 7:
		context_dict['landslide_risk_ls_s1_wb'] = 'Very High'
	elif context_dict['landslide_risk_ls_s1_wb'] >= 5 and context_dict['landslide_risk_ls_s1_wb'] < 7:
		context_dict['landslide_risk_ls_s1_wb'] = 'High'
	elif context_dict['landslide_risk_ls_s1_wb'] >= 4 and context_dict['landslide_risk_ls_s1_wb'] < 5:
		context_dict['landslide_risk_ls_s1_wb'] = 'Moderate'
	elif context_dict['landslide_risk_ls_s1_wb'] >= 2 and context_dict['landslide_risk_ls_s1_wb'] < 4:
		context_dict['landslide_risk_ls_s1_wb'] = 'Low'
	elif context_dict['landslide_risk_ls_s1_wb'] >= 1 and context_dict['landslide_risk_ls_s1_wb'] < 2:
		context_dict['landslide_risk_ls_s1_wb'] = 'Very Low'
	else :
		context_dict['landslide_risk_ls_s1_wb'] = 'None'

	if context_dict['landslide_risk_ls_s2_wb'] >= 7:
		context_dict['landslide_risk_ls_s2_wb'] = 'Very High'
	elif context_dict['landslide_risk_ls_s2_wb'] >= 5 and context_dict['landslide_risk_ls_s2_wb'] < 7:
		context_dict['landslide_risk_ls_s2_wb'] = 'High'
	elif context_dict['landslide_risk_ls_s2_wb'] >= 4 and context_dict['landslide_risk_ls_s2_wb'] < 5:
		context_dict['landslide_risk_ls_s2_wb'] = 'Moderate'
	elif context_dict['landslide_risk_ls_s2_wb'] >= 2 and context_dict['landslide_risk_ls_s2_wb'] < 4:
		context_dict['landslide_risk_ls_s2_wb'] = 'Low'
	elif context_dict['landslide_risk_ls_s2_wb'] >= 1 and context_dict['landslide_risk_ls_s2_wb'] < 2:
		context_dict['landslide_risk_ls_s2_wb'] = 'Very Low'
	else :
		context_dict['landslide_risk_ls_s2_wb'] = 'None'

	if context_dict['landslide_risk_ls_s3_wb'] >= 7:
		context_dict['landslide_risk_ls_s3_wb'] = 'Very High'
	elif context_dict['landslide_risk_ls_s3_wb'] >= 5 and context_dict['landslide_risk_ls_s3_wb'] < 7:
		context_dict['landslide_risk_ls_s3_wb'] = 'High'
	elif context_dict['landslide_risk_ls_s3_wb'] >= 4 and context_dict['landslide_risk_ls_s3_wb'] < 5:
		context_dict['landslide_risk_ls_s3_wb'] = 'Moderate'
	elif context_dict['landslide_risk_ls_s3_wb'] >= 2 and context_dict['landslide_risk_ls_s3_wb'] < 4:
		context_dict['landslide_risk_ls_s3_wb'] = 'Low'
	elif context_dict['landslide_risk_ls_s3_wb'] >= 1 and context_dict['landslide_risk_ls_s3_wb'] < 2:
		context_dict['landslide_risk_ls_s3_wb'] = 'Very Low'
	else :
		context_dict['landslide_risk_ls_s3_wb'] = 'None'

	context_dict.pop('position')

	return render_to_response(template,
								  RequestContext(request, context_dict))

def getLandslideInfoVillagesCommon(village):
	# template = './landslideinfo.html'
	# village = request.GET["v"]
	currentdate = datetime.datetime.utcnow()
	year = currentdate.strftime("%Y")
	month = currentdate.strftime("%m")
	day = currentdate.strftime("%d")

	context_dict = getCommonVillageData(village)

	px = get_object_or_404(AfgLspAffpplp, vuid=village)
	try:
		context_dict['landslide_risk'] = px.lsi_immap
	except:
		context_dict['landslide_risk'] = 0

	try:
		context_dict['landslide_risk_lsi_ku'] = px.lsi_ku
	except:
		context_dict['landslide_risk_lsi_ku'] = 0

	try:
		context_dict['landslide_risk_ls_s1_wb'] = px.ls_s1_wb
	except:
		context_dict['landslide_risk_ls_s1_wb'] = 0

	try:
		context_dict['landslide_risk_ls_s2_wb'] = px.ls_s2_wb
	except:
		context_dict['landslide_risk_ls_s2_wb'] = 0

	try:
		context_dict['landslide_risk_ls_s3_wb'] = px.ls_s3_wb
	except:
		context_dict['landslide_risk_ls_s3_wb'] = 0

	if context_dict['landslide_risk'] >= 7:
		context_dict['landslide_risk'] = 'Very High'
	elif context_dict['landslide_risk'] >= 5 and context_dict['landslide_risk'] < 7:
		context_dict['landslide_risk'] = 'High'
	elif context_dict['landslide_risk'] >= 4 and context_dict['landslide_risk'] < 5:
		context_dict['landslide_risk'] = 'Moderate'
	elif context_dict['landslide_risk'] >= 2 and context_dict['landslide_risk'] < 4:
		context_dict['landslide_risk'] = 'Low'
	elif context_dict['landslide_risk'] >= 1 and context_dict['landslide_risk'] < 2:
		context_dict['landslide_risk'] = 'Very Low'
	else :
		context_dict['landslide_risk'] = 'None'


	if context_dict['landslide_risk_lsi_ku'] >= 7:
		context_dict['landslide_risk_lsi_ku'] = 'Very High'
	elif context_dict['landslide_risk_lsi_ku'] >= 5 and context_dict['landslide_risk_lsi_ku'] < 7:
		context_dict['landslide_risk_lsi_ku'] = 'High'
	elif context_dict['landslide_risk_lsi_ku'] >= 4 and context_dict['landslide_risk_lsi_ku'] < 5:
		context_dict['landslide_risk_lsi_ku'] = 'Moderate'
	elif context_dict['landslide_risk_lsi_ku'] >= 2 and context_dict['landslide_risk_lsi_ku'] < 4:
		context_dict['landslide_risk_lsi_ku'] = 'Low'
	elif context_dict['landslide_risk_lsi_ku'] >= 1 and context_dict['landslide_risk_lsi_ku'] < 2:
		context_dict['landslide_risk_lsi_ku'] = 'Very Low'
	else :
		context_dict['landslide_risk_lsi_ku'] = 'None'

	if context_dict['landslide_risk_ls_s1_wb'] >= 7:
		context_dict['landslide_risk_ls_s1_wb'] = 'Very High'
	elif context_dict['landslide_risk_ls_s1_wb'] >= 5 and context_dict['landslide_risk_ls_s1_wb'] < 7:
		context_dict['landslide_risk_ls_s1_wb'] = 'High'
	elif context_dict['landslide_risk_ls_s1_wb'] >= 4 and context_dict['landslide_risk_ls_s1_wb'] < 5:
		context_dict['landslide_risk_ls_s1_wb'] = 'Moderate'
	elif context_dict['landslide_risk_ls_s1_wb'] >= 2 and context_dict['landslide_risk_ls_s1_wb'] < 4:
		context_dict['landslide_risk_ls_s1_wb'] = 'Low'
	elif context_dict['landslide_risk_ls_s1_wb'] >= 1 and context_dict['landslide_risk_ls_s1_wb'] < 2:
		context_dict['landslide_risk_ls_s1_wb'] = 'Very Low'
	else :
		context_dict['landslide_risk_ls_s1_wb'] = 'None'

	if context_dict['landslide_risk_ls_s2_wb'] >= 7:
		context_dict['landslide_risk_ls_s2_wb'] = 'Very High'
	elif context_dict['landslide_risk_ls_s2_wb'] >= 5 and context_dict['landslide_risk_ls_s2_wb'] < 7:
		context_dict['landslide_risk_ls_s2_wb'] = 'High'
	elif context_dict['landslide_risk_ls_s2_wb'] >= 4 and context_dict['landslide_risk_ls_s2_wb'] < 5:
		context_dict['landslide_risk_ls_s2_wb'] = 'Moderate'
	elif context_dict['landslide_risk_ls_s2_wb'] >= 2 and context_dict['landslide_risk_ls_s2_wb'] < 4:
		context_dict['landslide_risk_ls_s2_wb'] = 'Low'
	elif context_dict['landslide_risk_ls_s2_wb'] >= 1 and context_dict['landslide_risk_ls_s2_wb'] < 2:
		context_dict['landslide_risk_ls_s2_wb'] = 'Very Low'
	else :
		context_dict['landslide_risk_ls_s2_wb'] = 'None'

	if context_dict['landslide_risk_ls_s3_wb'] >= 7:
		context_dict['landslide_risk_ls_s3_wb'] = 'Very High'
	elif context_dict['landslide_risk_ls_s3_wb'] >= 5 and context_dict['landslide_risk_ls_s3_wb'] < 7:
		context_dict['landslide_risk_ls_s3_wb'] = 'High'
	elif context_dict['landslide_risk_ls_s3_wb'] >= 4 and context_dict['landslide_risk_ls_s3_wb'] < 5:
		context_dict['landslide_risk_ls_s3_wb'] = 'Moderate'
	elif context_dict['landslide_risk_ls_s3_wb'] >= 2 and context_dict['landslide_risk_ls_s3_wb'] < 4:
		context_dict['landslide_risk_ls_s3_wb'] = 'Low'
	elif context_dict['landslide_risk_ls_s3_wb'] >= 1 and context_dict['landslide_risk_ls_s3_wb'] < 2:
		context_dict['landslide_risk_ls_s3_wb'] = 'Very Low'
	else :
		context_dict['landslide_risk_ls_s3_wb'] = 'None'

	context_dict.pop('position')

	return context_dict

def dashboard_landslide(request, filterLock, flag, code, includes=[], excludes=[], response=dict_ext()):

	# response = dict_ext()

	if include_section('getCommonUse', includes, excludes):
		response.update(getCommonUse(request, flag, code))

	response['source'] = source = response.pathget('cache','getLandslideRisk') or dict_ext(getLandslideRisk(request, filterLock, flag, code, includes, excludes))
	response['panels'] = panels = dict_ext()
	baseline = response['source']['baseline']
	LANDSLIDE_TYPES_ORDER_EXC_VERYLOW = list_ext(LANDSLIDE_TYPES_ORDER).without(['very_low'])

	prefixes = ['lsi_immap','lsi_ku','ls_s1_wb','ls_s2_wb','ls_s3_wb',]
	chart_titles = {
		'lsi_immap':_('Landslide Indexes (iMMAP 2017)'),
		'lsi_ku':_('Multi-criteria Susceptibility Index'),
		'ls_s1_wb':_('Landslide Susceptibility (S1)'),
		'ls_s2_wb':_('Landslide Susceptibility (S2)'),
		'ls_s3_wb':_('Landslide Susceptibility (S3)'),
	}
	table_titles = {
		'lsi_immap':_('Population by Landslide Indexes (iMMAP 2017)'),
		'lsi_ku':_('Population by Multi-criteria Landslide Susceptibility Index'),
		'ls_s1_wb':_('Population by Landslide susceptibility - bedrock landslides in slow evolution (S1)'),
		'ls_s2_wb':_('Population by Landslide susceptibility - bedrock landslides in rapid evolution (S2)'),
		'ls_s3_wb':_('Population by Landslide susceptibility - cover material in rapid evolution (S3)'),
	}

	for p in prefixes:
		not_at_risk = baseline['pop_total']-sum([source.pathget(p,t) or 0 for t in LANDSLIDE_TYPES_ORDER_EXC_VERYLOW])
		
		panels.path('charts','donut')[p] = {
			'title':chart_titles[p],
			'child':[[LANDSLIDE_TYPES[t],source.pathget(p,t) or 0] for t in LANDSLIDE_TYPES_ORDER_EXC_VERYLOW]+[[_('Not at Risk'),not_at_risk]],
		}		
		panels.path('charts','bar')[p] = {
			'title':chart_titles[p],
			'labels':[LANDSLIDE_TYPES[t] for t in LANDSLIDE_TYPES_ORDER_EXC_VERYLOW],
			'values':[source.pathget(p,t) or 0 for t in LANDSLIDE_TYPES_ORDER_EXC_VERYLOW],
		}
		panels.path('tables')[p] = {
			'title':table_titles[p],
			'parentdata':[response['parent_label']]+[source.pathget(p,t) or 0 for t in LANDSLIDE_TYPES_ORDER_EXC_VERYLOW],
			'child':[{
				'value':[v['na_en']]+[v['%s_%s'%(p,t)] for t in LANDSLIDE_TYPES_ORDER_EXC_VERYLOW],
				'code':v['code'],
			} for v in source.pathget('lc_child') or []],
		}

	if include_section('GeoJson', includes, excludes):
		response['GeoJson'] = geojsonadd_landslide(response)

	return response

def geojsonadd_landslide(response):
	
	source = dict_ext(response['source'])
	boundary = source['GeoJson']
	source['lc_child_dict'] = {v['code']:v for v in source['lc_child']}

	LANDSLIDE_TYPES_ORDER_EXC_VERYLOW = list_ext(LANDSLIDE_TYPES_ORDER).without(['very_low'])

	for k,v in enumerate(boundary.get('features',[])):
		boundary['features'][k]['properties'] = prop = dict_ext(boundary['features'][k]['properties'])
		if response['areatype'] == 'district':
			response['set_jenk_divider'] = 1
			prop['na_en'] = response['parent_label']
			prop['value'] = 0
			prop.update({'%s_%s'%(i,t):source.pathget(i,t) for t in LANDSLIDE_TYPES_ORDER_EXC_VERYLOW for i in LANDSLIDE_INDEX_TYPES})

		else:
			response['set_jenk_divider'] = 7
			child = source['lc_child_dict'].get(prop['code'])
			if child:
				prop['na_en'] = child['na_en']
				prop['code'] = child['code']
				prop['value'] = 0
				prop.update({'%s_%s'%(i,t):child.get('%s_%s'%(i,t)) for t in LANDSLIDE_TYPES_ORDER_EXC_VERYLOW for i in LANDSLIDE_INDEX_TYPES})

	return boundary

def getLandslideStatistic(request,filterLock, flag, code):

	panels = dict_ext(dashboard_landslide(request, filterLock, flag, code)['panels'])
	panels_list = dict_ext()
	for k,v in panels['charts'].items():
		panels_list.path('charts')[k] = dict_ext(v).valueslistbykey(LANDSLIDE_INDEX_TYPES_ORDER,addkeyasattr=True)
	panels_list['tables'] = panels['tables'].valueslistbykey(LANDSLIDE_INDEX_TYPES_ORDER,addkeyasattr=True)

	return {'panels_list':panels_list}

class LandslideInfoVillages(Resource):

	class Meta:
		resource_name = 'landslide'
		authentication = SessionAuthentication()

	def prepend_urls(self):
		name = self._meta.resource_name
		return [
			url(r"^%s%s$" % (name, trailing_slash()), self.wrap_view('getdata'), name='get_%s'%(name)),
		]

	def getdata(self, request, **kwargs):
		self.method_check(request, allowed=['get'])
		self.is_authenticated(request)
		self.throttle_check(request)

		data = none_to_zero(getLandslideInfoVillagesCommon(request.GET.get('vuid')))

		LANDSLIDE_TITLE_ORDER = ['None']+[LANDSLIDE_TYPES[i] for i in LANDSLIDE_TYPES_ORDER]
		LANDSLIDE_INDEXES = ['landslide_risk','landslide_risk_lsi_ku','landslide_risk_ls_s1_wb','landslide_risk_ls_s2_wb','landslide_risk_ls_s3_wb',]
		values = {}
		for lsi in LANDSLIDE_INDEXES:
			values[lsi] = ['','','','','','',]
			values[lsi][LANDSLIDE_TITLE_ORDER.index(data[lsi])] = 'X'

		response = {
			'panels_list':{
				'tables':[
					{
						'key':'base_info',
						'child':[
							[_('Settlement'),data.get('name_en')],
							[_('District'),data.get('dist_na_en')],
							[_('Province'),data.get('prov_na_en')],
							[_('Area'),'{:,.1f} km2'.format((data.get('area_sqm') or 0)/1000000,)],
							[_('Total Population'),'{:,} km2'.format(data.get('area_population'))],
							[_('Number of Buildings'),'{:,} km2'.format(data.get('vuid_buildings'))],
						],
					},
					{
						'key':'landslide_susceptibility',
						'title':_('Landslide Susceptibility')+'*',
						'columntitles':[_('No Risk')]+[LANDSLIDE_TYPES[l] for l in LANDSLIDE_TYPES_ORDER],
						'child':[
							[_("Landslide Indexes (iMMAP 2017)"),]+values['landslide_risk'],
							[_("Multi-criteria Landslide Susceptibility Index")+'*',]+values['landslide_risk_lsi_ku'],
							[_("Landslide susceptibility - bedrock landslides in slow evolution (S1)")+'**',]+values['landslide_risk_ls_s1_wb'],
							[_("Landslide susceptibility - bedrock landslides in rapid evolution (S2)")+'**',]+values['landslide_risk_ls_s2_wb'],
							[_("Landslide susceptibility - cover material in rapid evolution (S3)")+'**',]+values['landslide_risk_ls_s3_wb'],
						],
						'footnotes':[
							'*'+_('University of Kansas / University of Nebraska Omaha. Nathan Schlagel, et al (2016)'),
							'**'+_('World Bank (2016)'),
						]
					},
				],
				'desc':[
					{
						'title':_("Multi-criteria Landslide Susceptibility Index"),
						'desc':[
							_("Layers were combined as a weighted overlay to create a landslide susceptibility index (LSI). Lithology, fault, river, and road data compiled by the USGS were derived from both pre- and mid-war sources of varying detail. A 10 year subset of earthquake data was used to reduce processing time; earthquake density was weighted by magnitude. An NDVI tile was used as vegetation data covering most of the country. Slope and aspect data were derived from 90m SRTM. Aspect and earthquake density diagrams not included because of their small scale features. Each factor was assigned weights for their own min-max range, and expected contribution to landslide susceptibility relative to each other developed through literature review.  Published studies of known landslides and corresponding Google Earth imagery were compared to same locations in the landslide susceptibility map")
						],
					},
					{
						'title':_("Resolution 500m"),
						'desc':[
							_("Observations Model results show high LSI values in areas with observed failures. Loess, granite, and schist/gneiss are the most susceptible lithologies with greatest risks in regions of high seismicity and faulting. Results appear to show slide deposits as lower susceptibility, and source slopes as higher, which may be used to assess reactivation potential. Such techniques can be widely applied. However, the uniqueness associated with assignment of relative weights to contributing factors makes models for any given location unique and inapplicable to other areas without alteration. Although advances in methodology and data quality would allow for improvements in landslide susceptibility analyses, comparisons in this study show that reasonable approximations can still be made with relatively coarse data sets")
						],
					},
					{
						'title':_("Landslide susceptibility - bedrock landslides in slow evolution (S1)"),
						'desc':[
							_("including: rotational slides, translational slides, earth flows and lateral spreading. Susceptibility values are represented according the following scale: 0=Null; 1-3=Low; 4-5=Moderate; 6=High; 7-9=Very High	"),
							_("Resolution: 30m. A spatial distribution of landslide susceptibility is defined using a GIS based, weighted scoring of contributing factors, including slope angle, lithology, landcover, terrain curvature, distance from geological faults, and distance from roads. These sources are modelled flow(run-out) and accumulation of debris areas to create landslide hazard maps"),
						],
					},
					{
						'title':_("Landslide susceptibility - bedrock landslides in rapid evolution (S2)"),
						'desc':[
							_("Afghanistan landslide susceptibility map for bedrock landslides in rapid evolution (S2), nationwide. This map shows the susceptibility for bedrock landslides in rapid evolution, including: falls and toppling. Susceptibility values are represented according the following scale: 0=Null; 1-3=Low; 4-5=Moderate; 6=High; 7-9=Very High")
						],
					},
					{
						'title':_("Landslide susceptibility - cover material in rapid evolution (S3) "),
						'desc':[
							_("Afghanistan landslide susceptibility map for cover material landslides in rapid evolution (S3), nationwide. This map shows the susceptibility for cover material landslides in rapid evolution, including: debris-mud flows. Susceptibility values are represented according the following scale: 0=Null; 1-3=Low; 4-5=Moderate; 6=High; 7-9=Very High")
						],
					},
				],
			},
		}

		return self.create_response(request, response)

def getQuickOverview(request, filterLock, flag, code, response=dict_ext()):
	
	response.path('cache')['getLandslideRisk'] = response.pathget('cache','getLandslideRisk') or getLandslideRisk(request, filterLock, flag, code, includes=['baseline','lsi'], response=response.within('cache'))
	dashboard_landslide_response = dashboard_landslide(request, filterLock, flag, code, includes=[''], response=response.within('cache','parent_label'))
	
	return {
		'templates':{
			'panels':'dash_qoview_landslide.html',
		},
		'data':{
			'panels':dict_ext(dashboard_landslide_response).pathget('panels'),
		},
	}
	