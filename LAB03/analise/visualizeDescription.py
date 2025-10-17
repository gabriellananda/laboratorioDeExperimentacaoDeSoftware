import pandas as pd
import matplotlib.pyplot as plt

# Carregar o dataset
df = pd.read_csv('prs_dataset.csv')

# Calcular a mediana da descrição por status
median_desc = df.groupby('status')['description_length'].median().sort_index()

# Gráfico de barras
plt.figure(figsize=(8, 6))
median_desc.plot(kind='bar', color=['#4C72B0', '#55A868'])
plt.title('Mediana do tamanho da descrição por status do PR')
plt.xlabel('Status do PR')
plt.ylabel('Descrição (nº de caracteres)')
plt.yscale('log')
plt.grid(axis='y', linestyle='--', alpha=0.7)
plt.tight_layout()
plt.savefig('bar_description_by_status.png')
plt.show()
