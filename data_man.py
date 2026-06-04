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
	return dataframe