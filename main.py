from osgeo import gdal, ogr
import sys, os, textwrap, math
import pandas as pd
from matplotlib import pyplot as plt
import cartopy.crs as ccrs
import cartopy.io.shapereader as shpreader
from cartopy.feature import ShapelyFeature

ogr.UseExceptions()

from_d = './from'
to_d = './to'
temp_d = './tmp'

# TODO peloamor use constantes
os.mkdir("./tmp")
os.mkdir("./tmp/modalidades")
os.mkdir("./tmp/modalidades_distritos")
os.mkdir("./tmp/modalidades_rasters")
os.mkdir("./to/modalidades_mapas")
os.mkdir("./to/modalidades_tabelas")
os.mkdir("./to/modalidades_graficos")
os.mkdir("./to/modalidades_graficos_redux")

print(from_d, '->', to_d)

distritos_vector: gdal.Dataset = ogr.Open("from/Acesso GIS/DISTRITOS_SIRGAS2000.shp")
acesso_vector: gdal.Dataset = ogr.Open("from/Acesso GIS/acess_spo.gpkg")
# acesso_vector: gdal.Dataset = ogr.Open("from/Acesso GIS/acess_spo_metros.gpkg")
# censo_vector: gdal.Dataset = ogr.Open("from/Acesso GIS/densidade_demografica.shp")

cidades_loc = "from/Acesso GIS/SP_Municipios_2025.shp"

acesso_layer: osgeo.ogr.Layer = acesso_vector.GetLayer(0)
# print(acesso_vector.GetProjectionRef())

tipos = {
	"CMA": "Indicador de acessibilidade cumulativo ativo",
	"CMP": "Indicador de acessibilidade cumulativo passivo",
	"TMI": "Indicador de tempo mínimo até oportunidade mais próxima"
}

indicadores = {
	"TT": "Para todos os empregos",
	"TB": "Para empregos de baixa escolaridade",
	"TM": "Para empregos de média escolaridade",
	"TA": "Para empregos de alta escolaridade",
	"ST": "Para todos os estabelecimentos de saúde",
	"SB": "Para estabelecimentos de sáude de baixa complexidade",
	"SM": "Para estabelecimentos de sáude de média complexidade",
	"SA": "Para estabelecimentos de sáude de alta complexidade",
	"ET": "Para todos os estabelecimentos de educação",
	"EI": "Para estabelecimentos de educação infantil",
	"EF": "Para estabelecimentos de educação fundamental",
	"EM": "Para estabelecimentos de educação média",
	"MT": "Para matrículas de todos níveis de ensino",
	"MI": "Para matrículas de ensino infantil",
	"MF": "Para matrículas de ensino fundamental",
	"MM": "Para matrículas de ensino médio",
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

transport_modes = {
	'bicycle': 'bicicleta',
	'walk': 'andando',
	'car': 'carro',
	'public_transport': 'transporte público'
}

years = { '2017': 2017, '2018': 2018, '2019': 2019 }

data_average_labels = [
	( 0000,(.0,0,0)),
	( 4000,(.1,0,0)),
	( 8000,(.2,0,0)),
	(12000,(.3,0,0)),
	(16000,(.4,0,0)),
	(20000,(.5,0,0)),
	(24000,(.6,0,0)),
	(28000,(.7,0,0)),
	(32000,(.8,0,0)),
	(36000,(.9,0,0)),
	(40000,(1 ,0,0))
]

data_by_population_labels = [
	( 00000,(.0,0,0)),
	( 20000,(.1,0,0)),
	( 40000,(.2,0,0)),
	( 60000,(.3,0,0)),
	( 80000,(.4,0,0)),
	(100000,(.5,0,0)),
	(120000,(.6,0,0)),
	(150000,(.7,0,0)),
	(180000,(.8,0,0))
]

# P001 pessoas no total ...
# CMAEF30 -> Número de escolas de ensino fundamental acessíveis em até 30 minutos

# print("Coletando lista de rótulos...")

feature_count = 0
for feature in acesso_layer:
	feature_count+=1
# 	if transport_modes.get(feature.mode) == None:
# 		transport_modes[feature.mode] = feature.mode
# 	pass
# 	year_s = str(int(feature.year))
# 	if years.get(year_s) == None:
# 		years[year_s] = int(feature.year)
# 	pass

# print('transport modes = ',transport_modes)
# print('years = ',years)
print('\nNúmero de features = ',feature_count)

INDICADORES_EXISTENTES = {}

def make_bar(title,x_axis,y_axis,filename):
	plt.figure(figsize=(20,25))
	plt.barh(x_axis,y_axis,color='purple',height=1)
	plt.yticks(rotation=15)
	plt.title("\n".join(textwrap.wrap(title,70)),loc='center',size=30)
	plt.tight_layout()
	plt.savefig('to/modalidades_graficos/'+filename+'.png')

	plt.figure()
	plt.yticks(rotation=15)
	plt.title("\n".join(textwrap.wrap(title + ' (mais baixos)',40)),loc='center',)
	plt.barh(x_axis[:15],y_axis[:15],color='purple',height=1)
	plt.tight_layout()
	plt.savefig('to/modalidades_graficos_redux/'+filename+'_least_'+'.png')

	plt.figure()
	plt.yticks(rotation=15)
	plt.title("\n".join(textwrap.wrap(title + ' (mais altos)',40)),loc='center',)
	plt.barh(x_axis[-15:],y_axis[-15:],color='purple',height=1)
	plt.tight_layout()
	plt.savefig('to/modalidades_graficos_redux/'+filename+'_most'+'.png')

	plt.figure(figsize=(10, 15), dpi=400)
	plt.yticks(rotation=15)
	plt.title("\n".join(textwrap.wrap(title + ' (mais altos e mais baixos)',40)),loc='center',)
	plt.barh(x_axis[:15],y_axis[:15],color='purple',height=1)
	plt.barh(x_axis[-15:],y_axis[-15:],color='purple',height=1)
	plt.tight_layout()
	plt.savefig('to/modalidades_graficos_redux/'+filename+'_both'+'.png')

def gen_table(data, modality: string, modality_description: string, year, transport_mode):
	dataframe = pd.DataFrame(columns=[
		'distrito_nome','distrito_sigla','data_times_sum','data_average',
		'data_by_population','hit_sum'
	])
	for index in data:
		dataframe.loc[index] = data[index]

	dataframe.to_excel('./to/modalidades_tabelas/' + modality + '_' + year + '_' + transport_mode +'.xlsx')
	dataframe = dataframe.sort_values('data_by_population')
	make_bar(modality_description + ' normalizado por densidade demográfica',dataframe['distrito_nome'],dataframe['data_by_population'],modality + '_' + year + '_' + transport_mode + "_population")
	dataframe = dataframe.sort_values('data_average')
	make_bar(modality_description + ' normalizado por pontos de referência',dataframe['distrito_nome'],dataframe['data_average'],modality + '_' + year + '_' + transport_mode + '_area')
	return dataframe

#FIXME talvez sejam os nomes normalizados q estejam zoando com os dados

def make_map(title, data_loc, indicador, data, info_col_name, labels: list(tuple(float,tuple(float,float,float)))):
	global cidades_loc
	plt.figure()
	ax: plt.Axes = plt.axes(projection=ccrs.PlateCarree())
	ax.set_extent([-46.95, -46.25, -23.35, -24.05], crs=ccrs.PlateCarree())
	# ax.coastlines()

	read = shpreader.Reader(cidades_loc)
	for geometry in read.geometries():
		shape_feature = ShapelyFeature(geometry,ccrs.PlateCarree(),
			facecolor=(.75,.75,.75),
			edgecolor=(.65,.65,.65)
		)
		ax.add_feature(shape_feature)

	read: shpreader.BasicReader = shpreader.Reader(data_loc)
	# print(read.records())
	
	for record in read.records():
		geometry = record.geometry
		# print(record._fields)
		# print(record.attributes)
		# print(data)
		distrito_data = data[data['distrito_nome'] == record.attributes['NOME_DIST']]
		# print(distrito_data.iloc[0])
		# print(distrito_data[info_col_name])
		col = None
		for i in range(0,len(labels)):
			# print(distrito_data.iloc[0][info_col_name])
			if labels[i][0] > distrito_data.iloc[0][info_col_name]:
				col = labels[i][1]
				break
		print(col)
		shape_feature = ShapelyFeature(geometry,ccrs.PlateCarree(),
			facecolor=col or (0,0,1),
			edgecolor=(.05,.05,.05)
		)
		ax.add_feature(shape_feature)
	
	plt.tight_layout()
	plt.savefig('./to/modalidades_mapas/' + title + '.png')
	# plt.show()
	exit(0)

def calculate_for_divisions(features: gdal.Dataset, modality: string, tipo, indicador, minuto, year, transport_mode):
	global distritos_vector, INDICADORES_EXISTENTES
	distritos_layer: ogr.Layer = distritos_vector.GetLayer()

	file_loc = "./tmp/modalidades_distritos/"+modality+'_'+year+'_'+transport_mode+".shp"
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

		data_average = 0
		if hit_sum > 0:
			data_average = data_sum / hit_sum

		# FIXME !!!!!!!
		# print(distrito_nome,'data avg',data_average)
		# print(hit_sum,':',data_sum)

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

	desc = (tipos[tipo] + ' ' + indicadores[indicador].lower() + ' ' + ' em ' + minutos[minuto] +
		' no modo de transporte ' + transport_modes[transport_mode] + ' no ano de ' + year)
	
	division_out.Close()
	print('')
	dataframe = gen_table(INDICADORES_EXISTENTES[modality]["data_divisions"],modality,desc, year, transport_mode)

	global data_average_labels, data_by_population_labels

	make_map(
		modality + '_' + year + '_' + transport_mode + "_average",
		file_loc, modality, dataframe, "data_average", data_average_labels
	)

	make_map(
		modality + '_' + year + '_' + transport_mode + "_population",
		file_loc, modality, dataframe, "data_by_population", data_by_population_labels
	)

	# gdal.Rasterize(
	# 	"./tmp/modalidades_raster/"+modality+'_'+year+'_'+transport_mode+".tiff",
	# 	file_loc,
	# 	format='png',
	# 	outputType=gdal.GDT_Int32,
	# 	noData=0,
	# 	initValues=0,
	# 	xRes=1024,
	# 	yRes=1024,
		
	# 	# allTouched=True,
	# 	attribute='data_by_population'
	# )
	# gdal.RasterizeLayer(
	# 	min = 1, max = 255,
	# 	format='png',
	# 	xRes=1024,
	# 	yRes=1024,
	# 	dataset=
	# )
	
	# png_driver = gdal.GetDRiverByName('png')
	# print(png_driver)
	# exit(0)

def fetch_modality(features, modality, tipo, indicador, minuto, year, transport_mode) -> gdal.Dataset:
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
		'data_divisions': {},
		'year':year,
		'transport_mode':transport_mode
	}

	file_loc = "./tmp/modalidades/"+modality+'_'+year+'_'+transport_mode+".shp"
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

	calculate_for_divisions(out, modality, tipo, indicador, minuto, year, transport_mode)
	out.Close()


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
				fetch_modality(features, modality, tipo, indicador, minuto, year, transport_mode)
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
