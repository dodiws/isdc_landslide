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

def getQuickOverview(request, filterLock, flag, code, includes=[], excludes=[]):
	response = {}
	response.update(getLandslideRisk(request, filterLock, flag, code, includes=['lsi_immap']))
	return response

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

def getLandslideRisk(request, filterLock, flag, code, includes=[], excludes=[]):
	response = dict_ext()
	# if include_section('getCommonUse', includes, excludes):
	#     response = getCommonUse(request, flag, code)
	if include_section('totals', includes, excludes):
		# targetBase = AfgLndcrva.objects.all()

		response['baseline'] = getBaseline(request, filterLock, flag, code, includes=['pop_lc','building_lc'])
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

	if include_section('lsi_immap', includes, excludes):
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

def dashboard_landslide(request, filterLock, flag, code, includes=[], excludes=[]):

	response = dict_ext()

	if include_section('getCommonUse', includes, excludes):
		response.update(getCommonUse(request, flag, code))

	response['source'] = source = dict_ext(getLandslideRisk(request, filterLock, flag, code, includes, excludes))
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
			'labels':[LANDSLIDE_TYPES[t] for t in LANDSLIDE_TYPES_ORDER_EXC_VERYLOW]+[_('Not at Risk')],
			'values':[source.pathget(p,t) or 0 for t in LANDSLIDE_TYPES_ORDER_EXC_VERYLOW]+[not_at_risk],
		}
		panels.path('tables')[p] = {
			'title':table_titles[p],
			'parentdata':[response['parent_label']]+[source.pathget(p,t) or 0 for t in LANDSLIDE_TYPES_ORDER_EXC_VERYLOW],
			'child':[{
				'value':[v['na_en']]+[v['%s_%s'%(p,t)] for t in LANDSLIDE_TYPES_ORDER_EXC_VERYLOW],
				'code':v['code'],
			} for v in source['lc_child']],
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
	for k,v in panels['charts'].items():
		v = dict_ext(v).valueslistbykey(LANDSLIDE_INDEX_TYPES_ORDER,addkeyasattr=True)
	panels['tables'] = panels['tables'].valueslistbykey(LANDSLIDE_INDEX_TYPES_ORDER,addkeyasattr=True)

	return {'panels_list':panels}
	