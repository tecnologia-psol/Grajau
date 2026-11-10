from osgeo import gdal, ogr
import sys, os, textwrap, math
import pandas as pd
from matplotlib import pyplot as plt, colors
import matplotlib
import data_vis, geo_utils, data_man

ogr.UseExceptions()
gdal.SetCacheMax(4000000000)

# TODO pós-processamento

from_d = './from'
to_d = './to'
temp_d = './tmp'

PROPERTIES = {
	"compile_centroids": False,
	"test_scale": False
}

for arg in sys.argv:
	if arg == '--compile-centroids':
		PROPERTIES["compile_centroids"] = True
	if arg == '--scale-test':
		PROPERTIES["test_scale"] = True

if PROPERTIES["test_scale"]:
	data_vis.set_limits(0,1000)
	x,r,g,b = [], [], [], []
	for i in range(0,1000):
		col = data_vis.get_color_rel(i)
		x.append(i)
		r.append(col[0])
		g.append(col[1])
		b.append(col[2])
	plt.plot(x,r,color='red')
	plt.plot(x,g,color='green')
	plt.plot(x,b,color='blue')
	plt.show()
	exit(0)

def trymkdir(dir):
	try:
		os.mkdir(dir)
	except:
		print(f'Não consegui criar o diretório {dir}')

# TODO peloamor use constantes

trymkdir("./tmp")
trymkdir("./tmp/modalidades")
trymkdir("./tmp/modalidades_distritos")
trymkdir("./to/modalidades_mapas")
trymkdir("./to/modalidades_mapas_normalizados")
trymkdir("./to/modalidades_tabelas")
trymkdir("./to/modalidades_tabelas_csv")
trymkdir("./to/modalidades_graficos")
trymkdir("./to/modalidades_graficos_redux")

print(from_d, '->', temp_d, '->', to_d)

distritos_vector: gdal.Dataset = ogr.Open("from/Acesso GIS/DISTRITOS_SIRGAS2000.shp")
acesso_vector: gdal.Dataset = ogr.Open("from/Acesso GIS/acess_spo.gpkg")

acesso_layer: osgeo.ogr.Layer = acesso_vector.GetLayer(0)

modality_filter = [
	r'\w{3}T[BMA]15.+', # Indicadores de emprego das varias escolaridades
	r'CMPPT+', # População
	r'CMAE\w+', # Estabelecimentos de ensino
	r'.*T00\d.*' # Quantidades de empregos de varias escolaridades
]

# Compila cada modalidade em um shapefile diferente

files = geo_utils.separate_categories(
	acesso_layer,
	distritos_vector.GetLayer(0),
	filter=modality_filter)

files = os.listdir('./tmp/modalidades_distritos')

# TODO: USA O NGC DE PASTAS LA QUE VC APRENDEU
# pasta_de_fotos_full = [PATH_SEP.join([PHOTO_DIR,p]) for p in pasta_de_fotos]

dist_stats = {}
cats = {}

for key in files:
	cats[key] = ogr.Open(files[key])

## TODO pelo amor ne essa pipeline ta um horror

for key in cats:
	category = cats[key]
	loc = geo_utils.compile_district_stats(category.GetLayer(0), distritos_vector.GetLayer(0), key)
	