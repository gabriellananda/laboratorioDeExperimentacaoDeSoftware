#!/usr/bin/env bash
set -euo pipefail

CSV_PATH="data/processed/github_top_1000_java_repositories.csv"
DEST_DIR="repos"
# Se nenhum limite for passado, clona todos os repositórios do CSV
if [ $# -eq 0 ]; then
  LIMIT=""
else
  LIMIT="$1"
fi

mkdir -p "$DEST_DIR"

if [ -z "$LIMIT" ]; then
  # Clona todos
  tail -n +2 "$CSV_PATH" | while IFS=',' read -r name owner url stars createdAt updatedAt; do
    repo_dir="$DEST_DIR/${owner}__${name}"
    if [ -d "$repo_dir/.git" ]; then
      echo "→ Já existe: $repo_dir (pulando)"
      continue
    fi
    echo "Clonando $owner/$name..."
    git clone --depth 1 "https://github.com/$owner/$name.git" "$repo_dir" || echo "✗ Falhou: $owner/$name"
  done
else
  # Clona apenas o limite especificado
  tail -n +2 "$CSV_PATH" | head -n "$LIMIT" | while IFS=',' read -r name owner url stars createdAt updatedAt; do
    repo_dir="$DEST_DIR/${owner}__${name}"
    if [ -d "$repo_dir/.git" ]; then
      echo "→ Já existe: $repo_dir (pulando)"
      continue
    fi
    echo "Clonando $owner/$name..."
    git clone --depth 1 "https://github.com/$owner/$name.git" "$repo_dir" || echo "✗ Falhou: $owner/$name"
  done
fi

echo "✓ Clone finalizado."
