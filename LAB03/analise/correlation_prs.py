import pandas as pd
from scipy.stats import spearmanr

# Carregar o dataset
df = pd.read_csv('prs_dataset.csv')

# Codificar o status: MERGED = 1, CLOSED = 0
df['status_num'] = df['status'].map({'MERGED': 1, 'CLOSED': 0})

# Teste de correlação de Spearman entre linhas adicionadas e status
corr_add, p_add = spearmanr(df['additions'], df['status_num'])
print(f"Correlação de Spearman entre linhas adicionadas e status do PR:")
print(f"Coeficiente: {corr_add:.4f}, p-valor: {p_add:.4e}")

# Teste de correlação de Spearman entre linhas removidas e status
corr_del, p_del = spearmanr(df['deletions'], df['status_num'])
print(f"\nCorrelação de Spearman entre linhas removidas e status do PR:")
print(f"Coeficiente: {corr_del:.4f}, p-valor: {p_del:.4e}")

# Teste de correlação de Spearman entre arquivos alterados e status
corr_files, p_files = spearmanr(df['changed_files'], df['status_num'])
print(f"\nCorrelação de Spearman entre arquivos alterados e status do PR:")
print(f"Coeficiente: {corr_files:.4f}, p-valor: {p_files:.4e}")