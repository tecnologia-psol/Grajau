import pandas as pd

def gen_table(data, category) -> pd.DataFrame:
	cols = []
	for index in data:
		for label in data[index]:
			cols.append(label)
		break
	dataframe = pd.DataFrame(columns=cols)
	for index in data:
		dataframe.loc[index] = data[index]

	dataframe.to_excel('./to/modalidades_tabelas/' + category +'.xlsx')
	dataframe.to_csv('./to/modalidades_tabelas_csv/' + category + '.csv')
	return dataframe