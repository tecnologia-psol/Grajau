from osgeo import gdal, ogr
import sys, os, textwrap, math
import pandas as pd
from matplotlib import pyplot as plt, colors
import matplotlib
import data_vis, geo_utils, data_man

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

cats = geo_utils.separate_categories(acesso_layer, distritos_vector.GetLayer(0))
dist_stats = {}

for key in cats:
	category = cats[key]
	loc = geo_utils.compile_category(category.GetLayer(0), distritos_vector.GetLayer(0), key)
	