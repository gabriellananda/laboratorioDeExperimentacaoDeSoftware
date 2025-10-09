import pandas as pd
import matplotlib.pyplot as plt

# Carregar o dataset
df = pd.read_csv('prs_dataset.csv')

# Boxplot do número de linhas adicionadas por status
plt.figure(figsize=(8, 6))
df.boxplot(column='additions', by='status')
plt.title('Distribuição do número de linhas adicionadas por status do PR')
plt.suptitle('')
plt.xlabel('Status do PR')
plt.ylabel('Linhas adicionadas')
plt.yscale('log')  # Escala log para melhor visualização
plt.savefig('boxplot_additions_by_status.png')
plt.show()

# Repita para deletions e changed_files se quiser comparar todas as métricas de tamanho