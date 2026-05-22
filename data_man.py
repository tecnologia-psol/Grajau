import pandas as pd

def gen_table(data, category):
	cols = []
	for index in data:
		for label in data[index]:
			cols.append(label)
		break
	dataframe = pd.DataFrame(columns=cols)
	for index in data:
		dataframe.loc[index] = data[index]

	dataframe.to_excel('./to/modalidades_tabelas/' + category +'.xlsx')
	# dataframe = dataframe.sort_values(DATA_BY_POPULATION_LABEL)
	# make_bar(description + ' normalizado por densidade demográfica',dataframe['distrito_nome'],dataframe[DATA_BY_POPULATION_LABEL],modality + '_' + year + '_' + transport_mode + "_population")
	# dataframe = dataframe.sort_values(DATA_AVG_LABEL)
	# make_bar(description + ' normalizado por pontos de referência',dataframe['distrito_nome'],dataframe[DATA_AVG_LABEL],modality + '_' + year + '_' + transport_mode + '_area')
	return dataframe