import pandas as pd
import matplotlib.pyplot as plt

df = pd.read_csv('prs_dataset.csv')

# Medianas por status
median_reviews = df.groupby('status')['reviews_count'].median().sort_index()
median_comments = df.groupby('status')['comments_count'].median().sort_index()

# Gráfico de revisões
plt.figure(figsize=(8, 6))
median_reviews.plot(kind='bar', color=['#E24A33', '#348ABD'])
plt.title('Mediana do número de revisões por status do PR')
plt.xlabel('Status do PR')
plt.ylabel('Número de revisões')
plt.grid(axis='y', linestyle='--', alpha=0.7)
plt.tight_layout()
plt.savefig('bar_reviews_by_status.png')
plt.show()

# Gráfico de comentários
plt.figure(figsize=(8, 6))
median_comments.plot(kind='bar', color=['#988ED5', '#777777'])
plt.title('Mediana do número de comentários por status do PR')
plt.xlabel('Status do PR')
plt.ylabel('Número de comentários')
plt.grid(axis='y', linestyle='--', alpha=0.7)
plt.tight_layout()
plt.savefig('bar_comments_by_status.png')
plt.show()
