import pandas as pd
import matplotlib.pyplot as plt

df = pd.read_csv('prs_dataset.csv')

plt.figure(figsize=(8, 6))
df.boxplot(column='time_to_close_seconds', by='status')
plt.title('Distribuição do tempo de análise por status do PR')
plt.suptitle('')
plt.xlabel('Status do PR')
plt.ylabel('Tempo de análise (segundos)')
plt.yscale('log')
plt.savefig('boxplot_time_by_status.png')
plt.show()