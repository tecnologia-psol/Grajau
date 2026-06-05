from osgeo import gdal, ogr
import sys, os, textwrap, math
import pandas as pd
from matplotlib import pyplot as plt, colors
import matplotlib
import data_vis, geo_utils, data_man

ogr.UseExceptions()

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

# TODO peloamor use constantes
os.mkdir("./tmp")
os.mkdir("./tmp/modalidades")
os.mkdir("./tmp/modalidades_distritos")
os.mkdir("./to/modalidades_mapas")
os.mkdir("./to/modalidades_mapas_normalizados")
os.mkdir("./to/modalidades_tabelas")
os.mkdir("./to/modalidades_tabelas_csv")
os.mkdir("./to/modalidades_graficos")
os.mkdir("./to/modalidades_graficos_redux")

print(from_d, '->', temp_d, '->', to_d)

distritos_vector: gdal.Dataset = ogr.Open("from/Acesso GIS/DISTRITOS_SIRGAS2000.shp")
acesso_vector: gdal.Dataset = ogr.Open("from/Acesso GIS/acess_spo.gpkg")

acesso_layer: osgeo.ogr.Layer = acesso_vector.GetLayer(0)

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

#compila as modalidades antes da filtragem
cats = geo_utils.separate_categories(acesso_layer, distritos_vector.GetLayer(0))
dist_stats = {}

for key in cats:
	category = cats[key]
	loc = geo_utils.compile_category(category.GetLayer(0), distritos_vector.GetLayer(0), key)
	