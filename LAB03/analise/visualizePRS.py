import pandas as pd
import matplotlib.pyplot as plt

df = pd.read_csv('prs_dataset.csv')

# Calcular medianas por status
median_add = df.groupby('status')['additions'].median().sort_index()
median_del = df.groupby('status')['deletions'].median().sort_index()
median_files = df.groupby('status')['changed_files'].median().sort_index()

# Gráfico de linhas adicionadas
plt.figure(figsize=(8, 6))
median_add.plot(kind='bar', color=['#66C2A5', '#FC8D62'])
plt.title('Mediana de linhas adicionadas por status do PR')
plt.xlabel('Status do PR')
plt.ylabel('Linhas adicionadas')
plt.yscale('log')
plt.grid(axis='y', linestyle='--', alpha=0.7)
plt.tight_layout()
plt.savefig('bar_additions_by_status.png')
plt.show()

# Gráfico de linhas removidas
plt.figure(figsize=(8, 6))
median_del.plot(kind='bar', color=['#8DA0CB', '#E78AC3'])
plt.title('Mediana de linhas removidas por status do PR')
plt.xlabel('Status do PR')
plt.ylabel('Linhas removidas')
plt.yscale('log')
plt.grid(axis='y', linestyle='--', alpha=0.7)
plt.tight_layout()
plt.savefig('bar_deletions_by_status.png')
plt.show()

# Gráfico de arquivos alterados
plt.figure(figsize=(8, 6))
median_files.plot(kind='bar', color=['#A6D854', '#FFD92F'])
plt.title('Mediana de arquivos alterados por status do PR')
plt.xlabel('Status do PR')
plt.ylabel('Arquivos alterados')
plt.yscale('log')
plt.grid(axis='y', linestyle='--', alpha=0.7)
plt.tight_layout()
plt.savefig('bar_changed_files_by_status.png')
plt.show()