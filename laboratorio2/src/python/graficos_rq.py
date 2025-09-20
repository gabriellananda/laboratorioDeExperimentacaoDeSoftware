import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
from datetime import datetime

# Carregue os dados
ck = pd.read_csv("data/processed/ck_summary.csv")
meta = pd.read_csv("data/processed/github_top_1000_java_repositories.csv")
meta["repo"] = meta["owner"] + "__" + meta["name"]
df = ck.merge(meta, on="repo")

# Calcule idade do repositório
if "createdAt" in df.columns:
    df['repo_age_years'] = (
        pd.Timestamp.now(tz=None) - pd.to_datetime(df['createdAt']).dt.tz_localize(None)
    ).dt.days / 365.25

# RQ01: Popularidade x Qualidade
sns.set(style="whitegrid")
plt.figure(figsize=(8,6))
sns.scatterplot(x=df["stars"], y=df["cbo_mean"], color="royalblue", alpha=0.6, edgecolor=None)
plt.xlabel("Popularidade (Estrelas)")
plt.ylabel("CBO (Acoplamento)")
plt.title("Popularidade dos Repositórios vs Acoplamento (CBO)")
plt.xscale("log")
plt.tight_layout()
plt.savefig("data/processed/stars_vs_cbo_mean_adaptado.png")
plt.close()

plt.figure(figsize=(8,6))
sns.scatterplot(x=df["stars"], y=df["dit_mean"], color="royalblue", alpha=0.6, edgecolor=None)
plt.xlabel("Popularidade (Estrelas)")
plt.ylabel("DIT (Profundidade de Herança)")
plt.title("Popularidade dos Repositórios vs Profundidade de Herança (DIT)")
plt.xscale("log")
plt.tight_layout()
plt.savefig("data/processed/stars_vs_dit_mean_adaptado.png")
plt.close()

plt.figure(figsize=(8,6))
sns.scatterplot(x=df["stars"], y=df["lcom_mean"], color="royalblue", alpha=0.6, edgecolor=None)
plt.xlabel("Popularidade (Estrelas)")
plt.ylabel("LCOM (Coesão)")
plt.title("Popularidade dos Repositórios vs Coesão (LCOM)")
plt.xscale("log")
plt.tight_layout()
plt.savefig("data/processed/stars_vs_lcom_mean_adaptado.png")
plt.close()

# RQ02: Maturidade x Qualidade
if "repo_age_years" in df.columns:
    plt.figure(figsize=(8,6))
    sns.regplot(x=df["repo_age_years"], y=df["dit_mean"], color="darkgreen", scatter_kws={'alpha':0.5})
    plt.xlabel("Idade do Repositório (anos)")
    plt.ylabel("DIT (Profundidade de Herança)")
    plt.title("Maturidade dos Repositórios vs Profundidade de Herança (DIT)")
    plt.tight_layout()
    plt.savefig("data/processed/repo_age_years_vs_dit_mean_adaptado.png")
    plt.close()

# RQ03: Atividade x Qualidade
if "releases" in df.columns:
    plt.figure(figsize=(8,6))
    sns.scatterplot(x=df["releases"], y=df["lcom_mean"], color="orange", alpha=0.6)
    plt.xlabel("Número de Releases")
    plt.ylabel("LCOM (Coesão)")
    plt.title("Atividade dos Repositórios vs Coesão (LCOM)")
    plt.xscale("log")
    plt.tight_layout()
    plt.savefig("data/processed/releases_vs_lcom_mean_adaptado.png")
    plt.close()

# RQ04: Tamanho x Qualidade
plt.figure(figsize=(8,6))
sns.jointplot(x=df["loc_mean"], y=df["cbo_mean"], kind="hex", color="purple")
plt.xlabel("LOC (Linhas de Código)")
plt.ylabel("CBO (Acoplamento)")
plt.title("Tamanho dos Repositórios vs Acoplamento (CBO)")
plt.xscale("log")
plt.tight_layout()
plt.savefig("data/processed/loc_mean_vs_cbo_mean_adaptado.png")
plt.close()

print("✓ Gráficos adaptados para cada RQ gerados.")
