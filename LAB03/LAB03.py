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

# Queries GraphQL para buscar informações
SEARCH_REPOS_QUERY = '''
query($first: Int!, $after: String) {
  search(query: "stars:>1 sort:stars-desc", type: REPOSITORY, first: $first, after: $after) {
    pageInfo { hasNextPage endCursor }
    nodes {
      ... on Repository {
        name
        owner { login }
        url
        stargazerCount
        createdAt
        updatedAt
      }
    }
  }
  rateLimit { remaining resetAt }
}
'''

# Query para buscar repositórios ordenados por estrelas. Usa paginação (first/after).
REPO_PR_COUNT_QUERY = '''
query($owner: String!, $name: String!) {
  repository(owner: $owner, name: $name) {
    pullRequests(states: [OPEN, CLOSED, MERGED]) { totalCount }
  }
  rateLimit { remaining resetAt }
}
'''
# Query para contar o total de pull requests de um repositório específico.
PULLS_PAGE_QUERY = '''
query($owner: String!, $name: String!, $first: Int!, $after: String) {
  repository(owner: $owner, name: $name) {
    pullRequests(states: [MERGED, CLOSED], first: $first, after: $after, orderBy: {field: CREATED_AT, direction: DESC}) {
      pageInfo { hasNextPage endCursor }
      nodes {
        number
        title
        url
        createdAt
        closedAt
        mergedAt
        additions
        deletions
        changedFiles
        bodyText
        author { login }
        reviews { totalCount }
        comments { totalCount }
        participants { totalCount }
      }
    }
  }
  rateLimit { remaining resetAt }
}
'''

# Função para executar consultas
def executeGraphqlQuery(query: str, variables: dict) -> Optional[dict]:
    payload = {"query": query, "variables": variables}
    try:
        r = requests.post(GRAPHQL_URL, headers=HEADERS, json=payload)
    except requests.RequestException as e:
        print("Erro de rede ao chamar GraphQL:", e)
        return None

    if r.status_code != 200:
        print(f"HTTP {r.status_code} - {r.text}")
        return None

    data = r.json()
    if "errors" in data:
        print("GraphQL errors:", data["errors"])
    return data