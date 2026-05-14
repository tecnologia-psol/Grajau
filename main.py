from osgeo import gdal, ogr
import sys, os, textwrap
import pandas as pd
from matplotlib import pyplot as plt

ogr.UseExceptions()

from_d = sys.argv[1]
to_d = sys.argv[2]
temp_d = './tmp'

# TODO peloamor faz constantes
os.mkdir("./tmp")
os.mkdir("./tmp/modalidades")
os.mkdir("./tmp/modalidades_distritos")
os.mkdir("./to/modalidades_mapas")
os.mkdir("./to/modalidades_tabelas")
os.mkdir("./to/modalidades_graficos")
os.mkdir("./to/modalidades_graficos_redux")

print(from_d, '->', to_d)

distritos_vector: gdal.Dataset = ogr.Open("from/Acesso GIS/DISTRITOS_SIRGAS2000.shp")
# acesso_vector: gdal.Dataset = ogr.Open("from/Acesso GIS/acess_spo.gpkg")
acesso_vector: gdal.Dataset = ogr.Open("from/Acesso GIS/acess_spo_metros.gpkg")
censo_vector: gdal.Dataset = ogr.Open("from/Acesso GIS/densidade_demografica.shp")

acesso_layer: osgeo.ogr.Layer = acesso_vector.GetLayer(0)
# print(acesso_vector.GetProjectionRef())

tipos = {
	"CMA": "Indicador de acessibilidade cumulativo ativo",
	"CMP": "Indicador de acessibilidade cumulativo passivo",
	"TMI": "Indicador de tempo mínimo até oportunidade mais próxima"
}

indicadores = {
	"TT": "Para todos os empregos",
	"TB": "Para empregos de baixa escolaridade indicador",
	"TM": "Para empregos de média escolaridade indicador",
	"TA": "Para empregos de alta escolaridade indicador",
	"ST": "Para todos os estabelecimentos de saúde indicadores",
	"SB": "Para estabelecimentos de sáude de baixa complexidade indicadores",
	"SM": "Para estabelecimentos de sáude de média complexidade indicadores",
	"SA": "Para estabelecimentos de sáude de alta complexidade indicadores",
	"ET": "Para todos os estabelecimentos de educação indicadores",
	"EI": "Para estabelecimentos de educação infantil indicadores",
	"EF": "Para estabelecimentos de educação fundamental indicadores",
	"EM": "Para estabelecimentos de educação média indicadores",
	"MT": "Para matrículas de todos níveis de ensino indicadores",
	"MI": "Para matrículas de ensino infantil indicadores",
	"MF": "Para matrículas de ensino fundamental indicadores",
	"MM": "Para matrículas de ensino médio indicadores",
	"CT": "Para todos os Centros de Referência da Assistência Social (CRAS)"
}

minutos = {
	"15": "15 minutos",
	"30": "30 minutos",
	"45": "45 minutos",
	"60": "60 minutos",
	"90": "90 minutos",
	"120": "120 minutos"
}

# P001 pessoas no total ...
# CMAEF30 -> Número de escolas de ensino fundamental acessíveis em até 30 minutos

transport_modes = {}
years = {}

print("Coletando lista de rótulos...")

feature_count = 0
for feature in acesso_layer:
	# print("mode ",feature)
	if transport_modes.get(feature.mode) == None:
		transport_modes[feature.mode] = feature.mode
	pass
	year_s = str(int(feature.year))
	if years.get(year_s) == None:
		years[year_s] = int(feature.year)
	pass
	feature_count+=1

print('transport modes = ',transport_modes)
print('years = ',years)
print('\nNúmero de features = ',feature_count)

INDICADORES_EXISTENTES = {}

def make_bar(title,x_axis,y_axis,filename):
	plt.figure(figsize=(13, 25), dpi=200)
	plt.barh(x_axis,y_axis,color='purple',height=1)
	plt.yticks(rotation=15)
	plt.title("\n".join(textwrap.wrap(title,40)),loc='center',)
	plt.savefig('to/modalidades_graficos/'+filename+'.png')
	plt.figure()
	plt.barh(x_axis[:15],y_axis[:15],color='purple',height=1)
	plt.savefig('to/modalidades_graficos_redux/'+filename+'_least_'+'.png')
	plt.figure()
	plt.barh(x_axis[-15:],y_axis[-15:],color='purple',height=1)
	plt.savefig('to/modalidades_graficos_redux/'+filename+'_most_'+'.png')
	plt.figure()
	# plt.barh(x_axis[-10:] + x_axis[:10],y_axis[-10:] + y_axis[:10],color='purple',height=1)
	
	plt.savefig('to/modalidades_graficos_redux/'+filename+'_both_'+'.png')

def gen_table(data, modality: string, modality_description: string):
	dataframe = pd.DataFrame(columns=[
		'distrito_nome','distrito_sigla','data_times_sum','data_average',
		'data_by_population','hit_sum'
	])
	for index in data:
		dataframe.loc[index] = data[index]
		
	dataframe.to_excel('./to/modalidades_tabelas/' + modality +'.xlsx')
	dataframe = dataframe.sort_values('data_by_population')
	make_bar(modality_description,dataframe['distrito_nome'],dataframe['data_by_population'],modality)

def calculate_for_divisions(features: gdal.Dataset, modality: string, tipo, indicador, minuto):
	global distritos_vector, INDICADORES_EXISTENTES
	distritos_layer: ogr.Layer = distritos_vector.GetLayer()

	file_loc = "./tmp/modalidades_distritos/"+modality+".shp"
	division_out: gdal.Dataset = gdal.GetDriverByName("ESRI Shapefile").Create(file_loc,0,0,1)
	layer: ogr.Layer = division_out.GetLayer()
	if not layer:
		layer = division_out.CreateLayer('l1')
	# centroid_layer: ogr.Layer = division_out.CreateLayer('centroids')
	# hex_layer: ogr.Layer = division_out.CreateLayer('hex')

	nome_field = ogr.FieldDefn("NOME_DIST", ogr.OFTString)
	sigla_field = ogr.FieldDefn("SIGLA_DIST", ogr.OFTString)
	data_sum_field = ogr.FieldDefn("data_sum", ogr.OFTReal)
	hit_sum_field = ogr.FieldDefn("hit_sum", ogr.OFTReal)
	data_times_field = ogr.FieldDefn("data_times_sum", ogr.OFTReal)
	data_average_field = ogr.FieldDefn("data_average",ogr.OFTReal)
	population_sum_field = ogr.FieldDefn("population_sum", ogr.OFTReal)
	data_by_population_field = ogr.FieldDefn("data_by_population", ogr.OFTReal)
	
	layer.CreateField(nome_field)
	layer.CreateField(sigla_field)
	layer.CreateField(data_sum_field)
	layer.CreateField(hit_sum_field)
	layer.CreateField(data_times_field)
	layer.CreateField(data_average_field)
	layer.CreateField(population_sum_field)
	layer.CreateField(data_by_population_field)

	print("Analisando distritos...",end=' ')
	
	distrito_count = 0
	for distrito_feature in distritos_layer:
		distrito_feature: ogr.Feature
		distrito_nome = distrito_feature['NOME_DIST']
		distrito_sigla = distrito_feature['SIGLA_DIST']
		distrito_geometry: ogr.Geometry = distrito_feature.geometry()

		population_sum = 0 # somatória da população de todos os hexágonos no distrito
		data_sum = 0 # somatória de todos os indices no distrito
		data_times_sum = 0 # somatória de todos (dado * população) no distrito
		hit_sum = 0 # numero de hexagonos em um distrito
		data_average = 0 # data_sum dividido pelo hit_sum

		print(distrito_nome,end='   ',flush=True)
		## FIXME Os pontos e os centroids tao saindo em lugares diferentes vou dormir flw
		feature_layer: ogr.Layer = features.GetLayer()
		for feature in feature_layer:
			feature: ogr.Feature
			geometry: ogr.Geometry = feature.geometry()
			centroid: ogr.Geometry = geometry.Centroid()
			# centroid_feature = ogr.Feature(ogr.FeatureDefn())
			# centroid_feature.SetGeometry(centroid)
			# centroid_layer.CreateFeature(centroid_feature)
			# hex_feature: ogr.Feature = ogr.Feature(ogr.FeatureDefn())
			# hex_feature.SetGeometry(geometry)
			# hex_layer.CreateFeature(hex_feature)
			if distrito_geometry.Contains(centroid):
				data_sum += feature["data"]
				population_sum += feature["population"]
				data_times_sum += feature["data_times"]
				hit_sum += 1
		
		defn = ogr.FeatureDefn()
		defn.AddFieldDefn(nome_field)
		defn.AddFieldDefn(sigla_field)
		defn.AddFieldDefn(data_sum_field)
		defn.AddFieldDefn(hit_sum_field)
		defn.AddFieldDefn(data_average_field)
		defn.AddFieldDefn(data_times_field)
		defn.AddFieldDefn(population_sum_field)
		defn.AddFieldDefn(data_by_population_field)
		new_feature = ogr.Feature(defn)

		data_by_population = 0
		if population_sum > 0:
			data_by_population = data_times_sum / population_sum

		if hit_sum > 0:
			data_average = data_sum / hit_sum

		table_data = {
			"distrito_nome": distrito_nome,
			"distrito_sigla": distrito_sigla,
			"data_sum": data_sum,
			"population_sum": population_sum,
			"data_times_sum": data_times_sum,
			"data_average": data_average,
			"data_by_population": data_by_population,
			"hit_sum": hit_sum
		}
		INDICADORES_EXISTENTES[modality]["data_divisions"][distrito_count] = table_data
		distrito_count += 1
		
		new_feature.SetField("data_sum",data_sum)
		new_feature.SetField("population_sum",population_sum)
		new_feature.SetField("data_times_sum",data_times_sum)
		new_feature.SetField("data_average",data_average)
		new_feature.SetField("data_by_population",data_by_population)
		new_feature.SetField("hit_sum",hit_sum)
		new_feature.SetField("NOME_DIST",distrito_nome)
		new_feature.SetField("SIGLA_DIST",distrito_sigla)
		new_feature.SetGeometry(distrito_geometry)
		layer.CreateFeature(new_feature)

	desc = tipos[tipo] + ' ' + indicadores[indicador].lower() + ' ' + ' em ' + minutos[minuto]
	gen_table(INDICADORES_EXISTENTES[modality]["data_divisions"],modality,desc)
	division_out.Close()
	print('')
	exit(0)

def fetch_modality(features, modality, tipo, indicador, minuto) -> gdal.Dataset:
	global INDICADORES_EXISTENTES
	feat_to_add = []

	density_field = ogr.FieldDefn("density", ogr.OFTReal )
	modality_field = ogr.FieldDefn("data", ogr.OFTReal )
	data_times_field = ogr.FieldDefn("data_times", ogr.OFTReal )
	area_field = ogr.FieldDefn("area", ogr.OFTReal ) 	 
	population_field = ogr.FieldDefn("population", ogr.OFTReal )

	for feature in features:
		feat_index = feature.GetFieldIndex(modality)
		if feat_index == -1:
			continue
		feat_data = feature.GetFieldAsString(feat_index)
		if feat_data == '':
			continue
		else:
			feat_to_add.append(feature.Clone())
	
	if len(feat_to_add) == 0:
		return


	modality = tipo + indicador + minuto
	human_readable = tipos[tipo] + ' - ' + indicadores[indicador] + ' - ' + minutos[minuto]
	
	INDICADORES_EXISTENTES[modality] = {
		'name': modality,
		'human_readable': human_readable,
		'data_divisions': {}
	}

	file_loc = "./tmp/modalidades/"+modality+".shp"
	out: gdal.Dataset = gdal.GetDriverByName("ESRI Shapefile").Create(file_loc,0,0,1)
	layer: ogr.Layer = out.GetLayer()
	if not layer:
		layer = out.CreateLayer('l1')
	layer.CreateField(modality_field)
	layer.CreateField(area_field)
	layer.CreateField(population_field)
	layer.CreateField(density_field)
	layer.CreateField(data_times_field)

	for feature in feat_to_add:
		feature: ogr.Feature
		geometry: ogr.Geometry = feature.GetGeometryRef()
		area = geometry.GeodesicArea()
		population = int(feature.GetField('P001'))
		data = feature.GetField(modality)
		data_times = population * data
		# print('area=',area)
		# print('population=',population)
		# print('data=',data)
		
		density = 0
		if area > 0:
			density = population / area
		
		defn = ogr.FeatureDefn()
		defn.AddFieldDefn(modality_field)
		defn.AddFieldDefn(area_field)
		defn.AddFieldDefn(population_field)
		defn.AddFieldDefn(density_field)
		defn.AddFieldDefn(data_times_field)

		feature_new: ogr.Feature = ogr.Feature(defn)
		feature_new.SetField("data",data)
		feature_new.SetField("area",area)
		feature_new.SetField("population",population)
		feature_new.SetField("density",density)
		feature_new.SetField("data_times",data_times)
		feature_new.SetGeometry(feature.geometry())
		
		layer.CreateFeature(feature_new)

	calculate_for_divisions(out, modality, tipo, indicador, minuto)
	out.Close()

	# gdal.Rasterize(
	# 	"./tmp/modalirasters/"+modality+".tiff",
	# 	file_loc,
	# 	format='GTIFF',
	# 	outputType=gdal.GDT_Byte,
	# 	noData=-1,
	# 	initValues=-1,
	# 	xRes=4096,
	# 	yRes=4096,
	# 	allTouched=True,
	# 	attribute='density'
	# )


def fetch_all_indicators(features,year,transport_mode):
	global tipos
	global indicadores
	global minutos
	for tipo in tipos:
		# print('tipo',tipo)
		for indicador in indicadores:
			# print('indicador',indicador)
			for minuto in minutos:
				# print('minuto',minuto)
				modality = tipo + indicador + minuto
				human_readable = tipos[tipo] + ' - ' + indicadores[indicador] + ' - ' + minutos[minuto]
				print("Compilando modalidade",modality,'(',human_readable,')')
				fetch_modality(features, modality, tipo, indicador, minuto)
	pass

def fetch_for_data(year, transport_mode):
	global acesso_layer
	print("Coletando dados para o ano",year,end='')
	print(" com modo de transporte",transport_mode)

	matching_feats = []

	for feature in acesso_layer:
		feat_year = feature.GetFieldAsString(feature.GetFieldIndex("year"))
		feat_mode = feature.GetFieldAsString(feature.GetFieldIndex("mode"))

		if feat_year == year and feat_mode == transport_mode:
			matching_feats.append(feature.Clone())
	
	print(len(matching_feats),'features encontradas')
	fetch_all_indicators(matching_feats,year,transport_mode)

for year in years:
	for transport_mode in transport_modes:
		fetch_for_data(year, transport_mode)
