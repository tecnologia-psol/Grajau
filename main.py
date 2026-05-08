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

modes = {}
years = {}

printf("Coletando lista de rótulos")
for feature in acesso_layer:
	# print("FEAT ",feature)
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
