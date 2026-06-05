import re as regex
from osgeo import gdal, ogr
import data_vis, data_man

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

# Do mapa de features hexagonais (meio que gerado como efeito colateral)
DATA_LABEL = "data" # Número do dado em específico
AREA_LABEL = "area"	# Área geodensica do hexágono
DENSITY_LABEL = "density" # População / Área
POPULATION_LABEL = "population" # População do distrito

HEXAGON_GRID_LABELS = [DATA_LABEL, AREA_LABEL, DENSITY_LABEL, POPULATION_LABEL]

# Do mapa de dados baseado nos distritos
DISTRICT_NAME_LABEL = "nome_dist" # also usado no mapa hexagonal para cachear o distrito
DISTRICT_ABBR_LABEL = "sigla_dist" 
DATA_AVG_LABEL = "data_avg"
DATA_SUM_LABEL = "data_sum"
DATA_TIMES_SUM_LABEL = "data_tsum" # Talvez nem seja bom deixar isso
POPULATION_SUM_LABEL = "population"
DATA_BY_POPULATION_LABEL = "data_popul"
HIT_SUM_LABEL = "hits"

GEO_LABELS = [
	DATA_AVG_LABEL,
	DATA_SUM_LABEL,
	DATA_TIMES_SUM_LABEL,
	POPULATION_SUM_LABEL,
	DATA_BY_POPULATION_LABEL
]

def generate_distr_fields():
	nome_field = ogr.FieldDefn(DISTRICT_NAME_LABEL, ogr.OFTString)
	sigla_field = ogr.FieldDefn(DISTRICT_ABBR_LABEL, ogr.OFTString)
	data_sum_field = ogr.FieldDefn(DATA_SUM_LABEL, ogr.OFTReal)
	hit_sum_field = ogr.FieldDefn(HIT_SUM_LABEL, ogr.OFTReal)
	data_times_field = ogr.FieldDefn(DATA_TIMES_SUM_LABEL, ogr.OFTReal)
	data_average_field = ogr.FieldDefn(DATA_AVG_LABEL,ogr.OFTReal)
	population_sum_field = ogr.FieldDefn(POPULATION_SUM_LABEL, ogr.OFTReal)
	data_by_population_field = ogr.FieldDefn(DATA_BY_POPULATION_LABEL, ogr.OFTReal)

	return [
		nome_field, sigla_field, data_sum_field, data_times_field, hit_sum_field,
		data_average_field, population_sum_field, data_by_population_field
	]

def gen_hex_fields():
	density_field = ogr.FieldDefn(DENSITY_LABEL, ogr.OFTReal )
	modality_field = ogr.FieldDefn(DATA_LABEL, ogr.OFTReal )
	area_field = ogr.FieldDefn(AREA_LABEL, ogr.OFTReal ) 	 
	population_field = ogr.FieldDefn(POPULATION_LABEL ,ogr.OFTReal )
	district_name_field = ogr.FieldDefn(DISTRICT_NAME_LABEL, ogr.OFTString )
	return [density_field, modality_field, area_field, population_field, district_name_field]

def gen_simple_feature(data_value, reference_feature, district_name) -> ogr.Feature:
	# Features do hex: Data, Area, Densidade e Populacao
	geometry: ogr.Geometry = reference_feature.GetGeometryRef()
	area = geometry.GeodesicArea()
	population = int(reference_feature.GetField('P001'))

	density = 0
	if area > 0:
		density = population / area
		
	defn = ogr.FeatureDefn()
	for field_def in gen_hex_fields():
		defn.AddFieldDefn(field_def)

	feature_new: ogr.Feature = ogr.Feature(defn)
	feature_new.SetField(DATA_LABEL,data_value)
	feature_new.SetField(AREA_LABEL,area)
	feature_new.SetField(POPULATION_LABEL,population)
	feature_new.SetField(DENSITY_LABEL,density)
	feature_new.SetField(DISTRICT_NAME_LABEL,district_name)
	feature_new.SetGeometry(reference_feature.geometry())
	return feature_new

def gen_distr_feature(geometry, info_tab):
	fields = generate_distr_fields()
	defn = ogr.FeatureDefn()
	for field in fields:
		defn.AddFieldDefn(field)
	feature_new: ogr.Feature = ogr.Feature(defn)
	for field in info_tab:
		feature_new.SetField(field,info_tab[field])
	feature_new.SetGeometry(geometry)
	return feature_new

def compile_category(hexes: ogr.Layer, districts: ogr.Layer, category_name: string) -> string:
	print(f"Calculando estatísticas distritais para a modalidade {category_name}")

	distr_fields = generate_distr_fields()
	shapefile_loc = 'tmp/modalidades_distritos/' + category_name + '_d.shp'
	
	dataset: gdal.Dataset = gdal.GetDriverByName("ESRI Shapefile").Create(shapefile_loc,0,0,1)
	layer: ogr.Layer = dataset.GetLayer() or dataset.CreateLayer('l1')
	
	for field in distr_fields:
		layer.CreateField(field)

	d_data = {}
	d_geometries = {}
	for district_feature in districts:
		district_feature: ogr.Feature
		d_data[district_feature['NOME_DIST']] = {
			DATA_SUM_LABEL: 0,
			POPULATION_SUM_LABEL: 0,
			HIT_SUM_LABEL: 0,
			DATA_AVG_LABEL: 0,
			DATA_BY_POPULATION_LABEL: 0,
			DISTRICT_NAME_LABEL: district_feature['NOME_DIST'],
			DISTRICT_ABBR_LABEL: district_feature['SIGLA_DIST']
		}
		d_geometries[district_feature['NOME_DIST']] = district_feature.geometry().Clone()

	miss_count = 0

	for hex_feature in hexes:
		hex_feature: ogr.Feature
		dname = hex_feature[DISTRICT_NAME_LABEL]
		if dname == 'IDK':
			miss_count += 1
			continue
		d_data[dname][DATA_SUM_LABEL] += hex_feature[DATA_LABEL]
		d_data[dname][HIT_SUM_LABEL] += 1
		d_data[dname][POPULATION_SUM_LABEL] += hex_feature[POPULATION_LABEL]

	for index in d_data:
		# Em tese não devem nunca ser 0, se é esse o caso provavelmente os de cima também são 0
		if d_data[index][HIT_SUM_LABEL] == 0: d_data[index][HIT_SUM_LABEL] = 1
		if d_data[index][POPULATION_SUM_LABEL] == 0: d_data[index][POPULATION_SUM_LABEL] = 1
		
		d_data[index][DATA_AVG_LABEL] = d_data[index][DATA_SUM_LABEL] / d_data[index][HIT_SUM_LABEL]
		d_data[index][DATA_BY_POPULATION_LABEL] = d_data[index][DATA_SUM_LABEL] / d_data[index][POPULATION_SUM_LABEL]

		feature_to_add = gen_distr_feature(d_geometries[index],d_data[index])
		layer.CreateFeature(feature_to_add)
	
	# TODO: queue em uma thread separada
	# Ou sla só salva a lista e faz no final
	data_table = data_man.gen_table(d_data,category_name)
	data_table = data_table.sort_values(DATA_AVG_LABEL)
	data_vis.make_bar(f'{category_name}_avg',data_table[DISTRICT_NAME_LABEL],data_table[DATA_AVG_LABEL],f'{category_name}_avg')
	data_table = data_table.sort_values(DATA_BY_POPULATION_LABEL)
	data_vis.make_bar(f'{category_name}_pop',data_table[DISTRICT_NAME_LABEL],data_table[DATA_BY_POPULATION_LABEL],f'{category_name}_pop')

	dataset.Close()

	# Mapas absolutos
	data_vis.make_map(f'{category_name}_pop',category_name,shapefile_loc,data_table,DATA_BY_POPULATION_LABEL,data_vis.get_color_for_population_abs)
	data_vis.make_map(f'{category_name}_avg',category_name,shapefile_loc,data_table,DATA_AVG_LABEL,data_vis.get_color_for_average_abs)

	# Mapas normalizados
	data_min = data_table.sort_values(DATA_BY_POPULATION_LABEL,ascending=True).iloc[0][DATA_BY_POPULATION_LABEL]
	data_max = data_table.sort_values(DATA_BY_POPULATION_LABEL,ascending=False).iloc[0][DATA_BY_POPULATION_LABEL]
	data_vis.set_limits(data_min,data_max)
	# print(f'{data_min},{data_max} p',data_vis.DATA_MIN,data_vis.DATA_MAX)
	data_vis.make_map(f'{category_name}_pop_norm',category_name,shapefile_loc,data_table,DATA_BY_POPULATION_LABEL,data_vis.get_color_rel,dir='./to/modalidades_mapas_normalizados/')
	
	data_min = data_table.sort_values(DATA_AVG_LABEL,ascending=True).iloc[0][DATA_AVG_LABEL]
	data_max = data_table.sort_values(DATA_AVG_LABEL,ascending=False).iloc[0][DATA_AVG_LABEL]
	data_vis.set_limits(data_min,data_max)
	# print(f'{data_min},{data_max} a',data_vis.DATA_MIN,data_vis.DATA_MAX)
	data_vis.make_map(f'{category_name}_avg_norm',category_name,shapefile_loc,data_table,DATA_AVG_LABEL,data_vis.get_color_rel,dir='./to/modalidades_mapas_normalizados/')

	return shapefile_loc

def compile_centroids(hexes: ogr.Layer):
	loc = 'tmp/centroids.shp'
	dataset: gdal.Dataset = gdal.GetDriverByName("ESRI Shapefile")
	layer: ogr.Layer = datasets[f_name].CreateLayer('l1')
	for hexg in hexes:
		hexg: ogr.Feature
		centroid: ogr.Geometry = hexg.geometry().Centroid()
		defn = ogr.FeatureDefn()
		n_feature = ogr.Feature(defn)
		n_feature.SetGeometry(centroid)
		layer.CreateFeature(n_feature)
	dataset.Close()

def separate_categories(hexes: ogr.Layer, districts: ogr.Layer):
	print("Separando categorias")
	datasets = {}
	file_locations = {}

	c, count = 0, hexes.GetFeatureCount()
	for feature in hexes:
		district_name = None
		for district in districts:
			district: ogr.Feature
			if district.geometry().Contains(feature.geometry().Centroid()):
				district_name = district['NOME_DIST']
				break
		c+=1
		if c > 100: break
		print(f'Processando feature {c}/{count} ({(100*c/count):.2f}%) ({len(datasets)} datasets)')
		feature: ogr.Feature
		fields = gen_hex_fields()
		derived_features = []
		for tipo in tipos:
			for indicador in indicadores:
				for minuto in minutos:
					year = feature.GetFieldAsString('year')
					mode = feature.GetFieldAsString('mode')
					modality = f'{tipo}{indicador}{minuto}'
					f_name = f'{modality}_{year}_{mode}'
					file_loc = 'tmp/modalidades/' + f_name + '.shp'
					feat_index = feature.GetFieldIndex(modality)
					if feat_index == -1: continue
					data_value = feature.GetFieldAsString(feat_index)
					if data_value == '': continue
					datasets[f_name] = datasets.get(f_name) or gdal.GetDriverByName("ESRI Shapefile").Create(file_loc,0,0,1)
					layer: ogr.Layer = datasets[f_name].GetLayer()
					if not layer:
						layer = datasets[f_name].CreateLayer('l1')
						for field in fields: layer.CreateField(field)
						
					file_locations[f_name] = file_locations.get(f_name) or file_loc
					layer.CreateFeature(gen_simple_feature(float(data_value),feature,district_name or 'IDK'))
	
	ret = {}
	for key in datasets:
		value: gdal.Dataset = datasets[key]
		value.Close()
		ret[key] = ogr.Open(file_locations[key])
	
	return ret
