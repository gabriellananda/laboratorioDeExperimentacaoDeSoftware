#!/usr/bin/env bash
set -euo pipefail

CSV_PATH="data/processed/github_top_1000_java_repositories.csv"
DEST_DIR="repos"
MISSING_LIST="missing.txt"

mkdir -p "$DEST_DIR"

# Função para clonar um bloco de até 100 repositórios
clone_block() {
  local block_file="$1"
  echo "--- Clonando bloco: $block_file ---"
  while read -r repo_id; do
    owner="${repo_id%%__*}"
    name="${repo_id##*__}"
    repo_dir="$DEST_DIR/${owner}__${name}"
    if [ -d "$repo_dir/.git" ]; then
      echo "→ Já existe: $repo_dir (pulando)"
      continue
    fi
    url=$(awk -F',' -v o="$owner" -v n="$name" '$1==n && $2==o {print $3}' "$CSV_PATH")
    if [ -z "$url" ]; then
      echo "✗ Não encontrado no CSV: $owner/$name"
      continue
    fi
    echo "Clonando $owner/$name..."
    git clone --depth 1 "$url" "$repo_dir" || echo "✗ Falhou: $owner/$name"
  done < "$block_file"
}

# Divide o arquivo missing.txt em blocos de 100
split -l 100 "$MISSING_LIST" missing_block_

# Para cada bloco, clona os repositórios
for block in missing_block_*; do
  clone_block "$block"
done

echo "✓ Clone dos faltantes em blocos finalizado."