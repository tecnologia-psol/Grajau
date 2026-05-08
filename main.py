from osgeo import gdal, ogr
import sys

from_d = sys.argv[1]
to_d = sys.argv[2]

print(from_d, '->', to_d)

g = gdal.Open("from/Acesso GIS/Acesso Raster.tif")
h = ogr.Open("from/Acesso GIS/SaoPaulo Distritos com Area.gpkg")

print('g',g)
print('h',h)

exit(0)