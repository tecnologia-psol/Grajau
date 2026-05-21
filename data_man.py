
def gen_table(data, modality, modality_description, year, transport_mode):
	dataframe = pd.DataFrame(columns=[
		'distrito_nome','distrito_sigla',DATA_TIMES_SUM_LABEL,DATA_AVG_LABEL,
		DATA_BY_POPULATION_LABEL,'hit_sum'
	])
	for index in data:
		dataframe.loc[index] = data[index]

	dataframe.to_excel('./to/modalidades_tabelas/' + modality + '_' + year + '_' + transport_mode +'.xlsx')
	dataframe = dataframe.sort_values(DATA_BY_POPULATION_LABEL)
	make_bar(modality_description + ' normalizado por densidade demográfica',dataframe['distrito_nome'],dataframe[DATA_BY_POPULATION_LABEL],modality + '_' + year + '_' + transport_mode + "_population")
	dataframe = dataframe.sort_values(DATA_AVG_LABEL)
	make_bar(modality_description + ' normalizado por pontos de referência',dataframe['distrito_nome'],dataframe[DATA_AVG_LABEL],modality + '_' + year + '_' + transport_mode + '_area')
	return dataframe