#!/usr/bin/env bash
set -euo pipefail

REPOS_DIR="repos"
RAW_DIR="data/raw"

for repo in "$REPOS_DIR"/*; do
  repo_name=$(basename "$repo")
  class_csv="$RAW_DIR/$repo_name/class.csv"
  if [ -d "$repo" ] && [ ! -f "$class_csv" ]; then
    echo "Rodando CK em: $repo"
    ./scripts/run_ck_one.sh "$repo" || echo "$repo_name" >> ck_failures.txt
  fi
done

echo "✓ CK rodado em todos os repositórios faltantes."