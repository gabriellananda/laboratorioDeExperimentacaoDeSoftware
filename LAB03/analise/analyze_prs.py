import pandas as pd

# Carregar o dataset
df = pd.read_csv('prs_dataset.csv')

# Visualizar as primeiras linhas
print("Primeiras linhas do dataset:")
print(df.head())

# Estatísticas descritivas das principais métricas
metrics = [
    'additions', 'deletions', 'changed_files', 'time_to_close_seconds',
    'description_length', 'reviews_count', 'comments_count', 'participants_count'
]

print("\nEstatísticas descritivas:")
print(df[metrics].describe())

print("\nMedianas das métricas:")
print(df[metrics].median())

# Contagem de PRs por status
print("\nContagem de PRs por status:")
print(df['status'].value_counts())

# Estatísticas separadas por status (MERGED/CLOSED)
for status in df['status'].unique():
    print(f"\nEstatísticas para PRs com status {status}:")
    print(df[df['status'] == status][metrics].describe())
    print("Medianas:")
    print(df[df['status'] == status][metrics].median())