import pandas as pd
import matplotlib.pyplot as plt

df = pd.read_csv('prs_dataset.csv')

# Boxplot do número de revisões por status
plt.figure(figsize=(8, 6))
df.boxplot(column='reviews_count', by='status')
plt.title('Distribuição do número de revisões por status do PR')
plt.suptitle('')
plt.xlabel('Status do PR')
plt.ylabel('Número de revisões')
plt.yscale('log')
plt.savefig('boxplot_reviews_by_status.png')
plt.show()

# Boxplot do número de comentários por status
plt.figure(figsize=(8, 6))
df.boxplot(column='comments_count', by='status')
plt.title('Distribuição do número de comentários por status do PR')
plt.suptitle('')
plt.xlabel('Status do PR')
plt.ylabel('Número de comentários')
plt.yscale('log')
plt.savefig('boxplot_comments_by_status.png')
plt.show()