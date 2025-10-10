import pandas as pd
from scipy.stats import spearmanr

df = pd.read_csv('prs_dataset.csv')
df['status_num'] = df['status'].map({'MERGED': 1, 'CLOSED': 0})

# Correlação entre número de revisões e status
corr_reviews, p_reviews = spearmanr(df['reviews_count'], df['status_num'])
print(f"Correlação de Spearman entre número de revisões e status do PR:")
print(f"Coeficiente: {corr_reviews:.4f}, p-valor: {p_reviews:.4e}")

# Correlação entre número de comentários e status
corr_comments, p_comments = spearmanr(df['comments_count'], df['status_num'])
print(f"\nCorrelação de Spearman entre número de comentários e status do PR:")
print(f"Coeficiente: {corr_comments:.4f}, p-valor: {p_comments:.4e}")