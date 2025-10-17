import pandas as pd
import matplotlib.pyplot as plt

df = pd.read_csv('prs_dataset.csv')

# Calcular mediana do tempo de fechamento por status
median_time = df.groupby('status')['time_to_close_seconds'].median().sort_index()

# Gráfico de barras
plt.figure(figsize=(8, 6))
median_time.plot(kind='bar', color=['#D55E00', '#009E73'])
plt.title('Mediana do tempo de análise por status do PR')
plt.xlabel('Status do PR')
plt.ylabel('Tempo de análise (segundos)')
plt.yscale('log')
plt.grid(axis='y', linestyle='--', alpha=0.7)
plt.tight_layout()
plt.savefig('bar_time_by_status.png')
plt.show()