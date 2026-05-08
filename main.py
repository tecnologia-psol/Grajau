from osgeo import gdal, ogr
import sys, os

ogr.UseExceptions()

from_d = sys.argv[1]
to_d = sys.argv[2]

if os.path.isdir("./tmp"):
	os.rmdir("./tmp")
os.mkdir("./tmp")

print(from_d, '->', to_d)

distritos_vector: gdal.Dataset = ogr.Open("from/Acesso GIS/SaoPaulo Distritos com Area.gpkg")
acesso_vector: gdal.Dataset = ogr.Open("from/Acesso GIS/acess_spo.gpkg")
censo_vector: gdal.Dataset = ogr.Open("from/Acesso GIS/densidade_demografica.shp")

acesso_layer: osgeo.ogr.Layer = acesso_vector.GetLayer(0)

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

# P001 pessoas no total ...

modes = {}
years = {}
indicadores = {}

print("Coletando lista de rótulos")

for feature in acesso_layer:
	print("FEAT ",feature); break
	# print(feature.year,feature.mode)
	if modes.get(feature.mode) == None:
		modes[feature.mode] = feature.mode
	pass
	year_s = str(int(feature.year))
	if years.get(year_s) == None:
		years[year_s] = int(feature.year)
	pass

print(modes)
print(years)

# print("layer",type(acesso_layer),acesso_layer);
