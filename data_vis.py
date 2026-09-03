import matplotlib.pyplot as plt
import matplotlib as mpl
import textwrap
import cartopy.crs as ccrs
import cartopy.io.shapereader as shpreader
from cartopy.feature import ShapelyFeature
import geo_utils
import numpy as np
import regex as re

cidades_loc = "from/Acesso GIS/SP_Municipios_2024.shp"

def make_bar(title,x_axis,y_axis,filename):
	plt.figure(figsize=(20,25))
	plt.barh(x_axis,y_axis,color='purple',height=1)
	plt.yticks(rotation=15)
	plt.title("\n".join(textwrap.wrap(title,70)),loc='center',size=30)
	plt.tight_layout()
	plt.savefig('to/modalidades_graficos/'+filename+'.png')
	plt.close()

	plt.figure()
	plt.yticks(rotation=15)
	plt.title("\n".join(textwrap.wrap(title + ' (mais baixos)',40)),loc='center',)
	plt.barh(x_axis[:15],y_axis[:15],color='purple',height=1)
	plt.tight_layout()
	plt.savefig('to/modalidades_graficos_redux/'+filename+'_least_'+'.png')
	plt.close()

	plt.figure()
	plt.yticks(rotation=15)
	plt.title("\n".join(textwrap.wrap(title + ' (mais altos)',40)),loc='center',)
	plt.barh(x_axis[-15:],y_axis[-15:],color='purple',height=1)
	plt.tight_layout()
	plt.savefig('to/modalidades_graficos_redux/'+filename+'_most'+'.png')
	plt.close()

	plt.figure(figsize=(10, 15), dpi=400)
	plt.yticks(rotation=15)
	plt.title("\n".join(textwrap.wrap(title + ' (mais altos e mais baixos)',40)),loc='center',)
	plt.barh(x_axis[:15],y_axis[:15],color='purple',height=1)
	plt.barh(x_axis[-15:],y_axis[-15:],color='purple',height=1)
	plt.tight_layout()
	plt.savefig('to/modalidades_graficos_redux/'+filename+'_both'+'.png')
	plt.close()


def linear_interpolate(min_,max_,value):
	return float((max_-min_) * min(value, 1) + min_)

def tuple_interpolate(min_, max_, value):
	if value > 1:
		print(f'ERRO: Valor de interpolação inválido: {value}')
	return (
		linear_interpolate(min_[0],max_[0],value),
		linear_interpolate(min_[1],max_[1],value),
		linear_interpolate(min_[2],max_[2],value)
	)

def get_color_for_population_abs(val):
	# 0-100
	keyframes = [
		(  0,(1,0 ,0)),
		(  2,(1,.5,0)),
		(  5,(1,1 ,0)),
		( 10,(0,1 ,0)),
		(100,(0,.2,0)),
		(10000,(.5,0,.5))
	]
	for i in range(1, len(keyframes)):
		if keyframes[i-1][0] <= val and val <= keyframes[i][0]:
			return tuple_interpolate(keyframes[i-1][1],keyframes[i][1],val/keyframes[len(keyframes)-1][0])
	return (0,0,1)

def get_color_for_average_abs(val):
	keyframes = [
		(     0,(1 , 0 , 0)),
		(   250,(1 ,.5, 0)),
		(   500,(1 ,1 , 0)),
		(  2500,(0 ,1 , 0)),
		( 10000,(0 ,.2, 0)),
		(100000,(.5,0 ,.5))
	]
	for i in range(1, len(keyframes)):
		if keyframes[i-1][0] <= val and val <= keyframes[i][0]:
			return tuple_interpolate(keyframes[i-1][1],keyframes[i][1],val/keyframes[len(keyframes)-1][0])
	return (0,0,1)

DATA_MIN = 0
DATA_MAX = 1

def set_limits(data_min, data_max):
	global DATA_MIN, DATA_MAX
	DATA_MIN = data_min
	DATA_MAX = data_max

def get_color_rel(val):
	global DATA_MIN, DATA_MAX
	keyframes = [
		(    0,(1, 0 ,0)),
		(    2,(1,.5,0 )),
		(    5,(1,1 ,0 )),
		(   10,(0,1 ,0 )),
		(100.1,(0,.4,0 ))
	]
	k_len = len(keyframes)
	max_key = 100
	n_val = max_key * (val-DATA_MIN) / (DATA_MAX - DATA_MIN)

	for i in range(1, len(keyframes)):
		# print(f'comparando {n_val} <= {keyframes[i][0]}')
		if n_val <= keyframes[i][0]:
			normal_for_subinterval = (n_val - keyframes[i-1][0])/(keyframes[i][0]-keyframes[i-1][0])
			return tuple_interpolate(keyframes[i-1][1],keyframes[i][1],normal_for_subinterval)
	# raise Exception(f'ERRO: ERRO DE INTERPOLAÇÃO, valor ({val}->{n_val}) é maior que {max_key}')
	print(f'ERRO: ERRO DE INTERPOLAÇÃO, valor ({val}->{n_val}) é maior que {max_key}')
	# return (0,0,1) # Teoricamente impossível
	return keyframes[k_len - 1]

def make_colormap(color_function,min,max,step):
	arr = []
	i = min
	while i < max:
		v = np.asarray(color_function(i))
		arr.append(v)
		# print(f'{i} -> ({v[0]:.2f} {v[1]:.2f} {v[2]:.2f})')
		i += step

	map = mpl.colors.ListedColormap(np.array(arr))
	return map

def make_map(filename, title, vector_loc, data, info_col_name, color_function, dir = './to/modalidades_mapas/', **kwargs):
	global cidades_loc, DATA_MIN, DATA_MAX
	fig = plt.figure(dpi=200)

	rmin = kwargs.get('rmin',DATA_MIN)
	rmax = kwargs.get('rmax',DATA_MAX)

	# plt.subplot(1, 2, 1)
	ax: plt.Axes = plt.axes(projection=ccrs.PlateCarree())
	ax.set_extent([-46.95, -46.25, -23.35, -24.05], crs=ccrs.PlateCarree())
	plt.title("\n".join(textwrap.wrap(title,70)),loc='center',size=12)

	# Coloca os municipios de São Paulo no fundo
	read = shpreader.Reader(cidades_loc)
	for geometry in read.geometries():
		shape_feature = ShapelyFeature(geometry,ccrs.PlateCarree(),
			facecolor=(.75,.75,.75),
			edgecolor=(.65,.65,.65)
		)
		ax.add_feature(shape_feature)

	read: shpreader.BasicReader = shpreader.Reader(vector_loc)
	
	for record in read.records():
		geometry = record.geometry
		distrito_data = data[data[geo_utils.DISTRICT_NAME_LABEL] == record.attributes[geo_utils.DISTRICT_NAME_LABEL]]
		color = color_function(distrito_data.iloc[0][info_col_name])
		if color[0] > 1 or color[1] > 1 or color[2] > 1: return
		shape_feature = ShapelyFeature(geometry,ccrs.PlateCarree(),
			facecolor=color or (0,0,1),
			edgecolor=(.05,.05,.05)
		)
		ax.add_feature(shape_feature)
	
	# cmap = mpl.cm.cool
	cmap = make_colormap(color_function,rmin,rmax,(rmax-rmin)/ 100.0)
	# print(f"{cmap}, {cmap.colors}")
	norm = mpl.colors.Normalize(vmin=rmin, vmax=rmax)
	fig.colorbar(mpl.cm.ScalarMappable(norm=norm, cmap=cmap),
				ax=ax, orientation='vertical', label=f'{info_col_name}')
	
	plt.tight_layout()
	plt.savefig(dir + filename + '.png')
	plt.close()