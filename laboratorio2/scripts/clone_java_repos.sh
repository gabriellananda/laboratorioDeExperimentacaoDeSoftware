#!/usr/bin/env bash
set -euo pipefail

CSV_PATH="data/processed/github_top_1000_java_repositories.csv"
DEST_DIR="repos"
LIMIT="${1:-1}"    # quantos clonar (default = 1)

mkdir -p "$DEST_DIR"

tail -n +2 "$CSV_PATH" | head -n "$LIMIT" | while IFS=',' read -r name owner url stars createdAt updatedAt; do
  repo_dir="$DEST_DIR/${owner}__${name}"
  if [ -d "$repo_dir/.git" ]; then
    echo "→ Já existe: $repo_dir (pulando)"
    continue
  fi
  echo "Clonando $owner/$name..."
  git clone --depth 1 "https://github.com/$owner/$name.git" "$repo_dir" || echo "✗ Falhou: $owner/$name"
done

echo "✓ Clone finalizado."
