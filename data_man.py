import pandas as pd
import os

def gen_table(data, category) -> str:
	cols = []
	for index in data:
		for label in data[index]:
			cols.append(label)
		break
	dataframe = pd.DataFrame(columns=cols)
	for index in data:
		dataframe.loc[index] = data[index]

	xlsl_loc = './to/modalidades_tabelas/' + category +'.xlsx'
	if os.path.isfile(xlsl_loc):
		print(f'{xlsl_loc} já existe, pulando')
		return xlsl_loc
	dataframe.to_excel(xlsl_loc)
	dataframe.to_csv('./to/modalidades_tabelas_csv/' + category + '.csv')
	return xlsl_loc