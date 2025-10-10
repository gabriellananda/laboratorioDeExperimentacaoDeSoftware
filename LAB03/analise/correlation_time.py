import pandas as pd
from scipy.stats import spearmanr

df = pd.read_csv('prs_dataset.csv')
df['status_num'] = df['status'].map({'MERGED': 1, 'CLOSED': 0})

corr_time, p_time = spearmanr(df['time_to_close_seconds'], df['status_num'])
print(f"Correlação de Spearman entre tempo de análise e status do PR:")
print(f"Coeficiente: {corr_time:.4f}, p-valor: {p_time:.4e}")