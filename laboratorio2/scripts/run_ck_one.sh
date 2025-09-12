#!/usr/bin/env bash
set -euo pipefail

REPO_PATH="${1:-}"
if [ -z "$REPO_PATH" ]; then
  echo "Uso: ./scripts/run_ck_one.sh repos/OWNER__NAME"
  exit 1
fi

# Java 17
export JAVA_HOME=/usr/lib/jvm/java-17-openjdk-amd64
export PATH="$JAVA_HOME/bin:$PATH"

# Caminho absoluto do JAR do CK
CK_JAR="$(cd .. && pwd)/ck/target/ck-0.7.1-SNAPSHOT-jar-with-dependencies.jar"

# Caminhos absolutos
LAB2_DIR="$(pwd)"
ABS_REPO="$LAB2_DIR/$REPO_PATH"
REPO_NAME="$(basename "$REPO_PATH")"
OUT_BASE="$LAB2_DIR/data/raw"
OUT_DIR="$OUT_BASE/$REPO_NAME"

mkdir -p "$OUT_DIR"

echo ">> Rodando CK em: $ABS_REPO"
echo ">> Saída esperada: $OUT_DIR"

# Execução do CK
# (useJars=true, maxAtOnce=0, variablesAndFields=true para gerar todos CSVs possíveis)
java -jar "$CK_JAR" "$ABS_REPO" true 0 true "$OUT_DIR" || true

# Alguns CKs gravam no OUT_BASE com prefixo do repo. Normalizamos:
# 1) mover quaisquer arquivos prefixados no OUT_BASE para OUT_DIR
shopt -s nullglob
for f in "$OUT_BASE/${REPO_NAME}"*.csv; do
  mv "$f" "$OUT_DIR/"
done

# 2) renomear arquivos para nomes simples (se existirem)
declare -A MAP=( ["class"]="class" ["method"]="method" ["field"]="field" ["variable"]="variable" )
for kind in "${!MAP[@]}"; do
  src="$OUT_DIR/${REPO_NAME}${kind}.csv"
  [ -f "$src" ] && mv "$src" "$OUT_DIR/${MAP[$kind]}.csv"
done
shopt -u nullglob

echo "✓ Arquivos no diretório final:"
ls -la "$OUT_DIR"
