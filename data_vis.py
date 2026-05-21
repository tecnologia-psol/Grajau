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


def linear_interpolate(min_,max_,value):
	# print(min_,max_,value,"o-o",float((max_-min_) * value + min_))
	return float((max_-min_) * value + min_)

def tuple_interpolate(min_, max_, value):
	return (
		linear_interpolate(min_[0],max_[0],value),
		linear_interpolate(min_[1],max_[1],value),
		linear_interpolate(min_[2],max_[2],value)
	)

def get_color_for_population(val):
	# 0-100
	keyframes = [
		(  0,(1,0 ,0)),
		(  2,(1,.5,0)),
		(  5,(1,1 ,0)),
		( 10,(0,1 ,0)),
		(100,(0,.2,0))
	]
	for i in range(1, len(keyframes)):
		if keyframes[i-1][0] <= val and val <= keyframes[i][0]:
			return tuple_interpolate(keyframes[i-1][1],keyframes[i][1],val/keyframes[len(keyframes)-1][0])
	return (0,0,1)

def get_color_for_average(val):
	return(0,0,1)

def make_map(filename, title, data_loc, indicador, data, info_col_name, color_function):
	global cidades_loc
	plt.figure(dpi=200)
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

	read: shpreader.BasicReader = shpreader.Reader(data_loc)
	
	for record in read.records():
		geometry = record.geometry
		distrito_data = data[data['distrito_nome'] == record.attributes['NOME_DIST']]
		color = get_color_for_population(distrito_data.iloc[0][info_col_name])
		shape_feature = ShapelyFeature(geometry,ccrs.PlateCarree(),
			facecolor=color or (0,0,1),
			edgecolor=(.05,.05,.05)
		)
		ax.add_feature(shape_feature)

	plt.tight_layout()
	plt.savefig('./to/modalidades_mapas/' + filename + '.png')