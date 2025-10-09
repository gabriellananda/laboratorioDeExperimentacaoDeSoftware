import pandas as pd
import matplotlib.pyplot as plt

df = pd.read_csv('prs_dataset.csv')

plt.figure(figsize=(8, 6))
df.boxplot(column='description_length', by='status')
plt.title('Distribuição do tamanho da descrição por status do PR')
plt.suptitle('')
plt.xlabel('Status do PR')
plt.ylabel('Descrição (nº de caracteres)')
plt.yscale('log')
plt.savefig('boxplot_description_by_status.png')
plt.show()