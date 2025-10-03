import os
import sys
import time
import csv
import math
import requests
from datetime import datetime, timezone
from typing import Optional, List

#Configurações do token
GITHUB_TOKEN = ""  # <<< coloque seu token aqui
if not GITHUB_TOKEN:
    print("ERRO: variável de ambiente GITHUB_TOKEN não encontrada. Exporte seu token do GitHub e rode novamente.")
    sys.exit(1)

#URL da API GraphQL do Github
GRAPHQL_URL = "https://api.github.com/graphql"
HEADERS = {"Authorization": f"Bearer {GITHUB_TOKEN}", "Content-Type": "application/json"}

# Parâmetros para as consultas e filtros
TOP_REPOS_LIMIT = 200      # buscar os 200 repositórios mais populares
MIN_PR_COUNT = 100         # repositórios com pelo menos 100 PRs (merged + closed)
MIN_PR_DURATION_SECONDS = 60 * 60  # PRs cuja diferença entre createdAt e closed/merged > 1 hora

# Arquivos de saída
REPOS_CSV = "selected_repos.csv"
PRS_CSV = "prs_dataset.csv"