import pandas as pd
from scipy.stats import spearmanr

df = pd.read_csv('prs_dataset.csv')
df['status_num'] = df['status'].map({'MERGED': 1, 'CLOSED': 0})

corr_desc, p_desc = spearmanr(df['description_length'], df['status_num'])
print(f"Correlação de Spearman entre tamanho da descrição e status do PR:")
print(f"Coeficiente: {corr_desc:.4f}, p-valor: {p_desc:.4e}")