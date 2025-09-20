import os
import pandas as pd
from pathlib import Path
from summarize_ck import summarize_repo

RAW_DIR = "data/raw"
OUT_CSV = "data/processed/ck_summary.csv"

all_stats = []

for repo_dir in Path(RAW_DIR).iterdir():
    if repo_dir.is_dir() and (repo_dir / "class.csv").exists():
        try:
            # Sumariza e retorna o dict de stats
            stats = summarize_repo(repo_dir, None)  # Ajuste summarize_ck.py para retornar stats se out_csv=None
            all_stats.append(stats)
        except Exception as e:
            print(f"Erro em {repo_dir.name}: {e}")

# Salva tudo em um único CSV
df = pd.DataFrame(all_stats)
df.to_csv(OUT_CSV, index=False)
print(f"✓ Sumarização agregada salva em {OUT_CSV}")