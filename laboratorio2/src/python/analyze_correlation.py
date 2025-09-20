import pandas as pd
import seaborn as sns
import matplotlib.pyplot as plt
from scipy.stats import spearmanr, pearsonr
from datetime import datetime

# Carregue os dados
ck = pd.read_csv("data/processed/ck_summary.csv")
meta = pd.read_csv("data/processed/github_top_1000_java_repositories.csv")

# Ajuste o nome do repositório para merge
meta["repo"] = meta["owner"] + "__" + meta["name"]
df = ck.merge(meta, on="repo")


# Calcule idade do repositório em anos (corrigido para evitar erro de tz-naive/tz-aware)
df['repo_age_years'] = (
	pd.Timestamp.now(tz=None) - pd.to_datetime(df['createdAt']).dt.tz_localize(None)
).dt.days / 365.25

# Adicione releases, loc, comments se disponível
process_metrics = ["stars", "repo_age_years"]
if "releases" in df.columns:
	process_metrics.append("releases")
if "loc_mean" in df.columns:
	process_metrics.append("loc_mean")
if "comments_mean" in df.columns:
	process_metrics.append("comments_mean")

quality_metrics = ["cbo_mean", "dit_mean", "lcom_mean"]

# Função para calcular correlação e gerar gráfico
for p_metric in process_metrics:
	for q_metric in quality_metrics:
		if p_metric in df.columns and q_metric in df.columns:
			# Correlação de Spearman
			corr_s, pval_s = spearmanr(df[p_metric], df[q_metric], nan_policy='omit')
			# Correlação de Pearson
			corr_p, pval_p = pearsonr(df[p_metric].fillna(0), df[q_metric].fillna(0))
			print(f"Spearman {p_metric} x {q_metric}: corr={corr_s:.3f}, p={pval_s:.3g}")
			print(f"Pearson  {p_metric} x {q_metric}: corr={corr_p:.3f}, p={pval_p:.3g}")
			# Gráfico
			plt.figure(figsize=(7,5))
			sns.scatterplot(x=p_metric, y=q_metric, data=df)
			plt.title(f"{p_metric} vs {q_metric}")
			plt.tight_layout()
			plt.savefig(f"data/processed/{p_metric}_vs_{q_metric}.png")
			plt.close()

print("✓ Análise de correlação e gráficos concluída.")