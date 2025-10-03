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

# Função para pegar repositórios populares/selecionados
def getTopRepositories(limit: int = TOP_REPOS_LIMIT) -> List[dict]:
    repositories = []
    cursor = None
    fetched = 0
    page_size = 50  # buscar em páginas de 50

    print(f"Buscando top {limit} repositórios (paginando em {page_size})...")
    while fetched < limit:
        to_fetch = min(page_size, limit - fetched)
        variables = {"first": to_fetch, "after": cursor}
        resp = executeGraphqlQuery(SEARCH_REPOS_QUERY, variables)
        if not resp or "data" not in resp:
            print("Erro ao buscar repositórios. Encerrando busca.")
            break
        rate_info = resp["data"].get("rateLimit")
        waitIfRateLimited(rate_info)

        search = resp["data"]["search"]
        nodes = search["nodes"]
        for n in nodes:
            repositories.append(n)
        fetched += len(nodes)

        if not search["pageInfo"]["hasNextPage"]:
            break
        cursor = search["pageInfo"]["endCursor"]
        time.sleep(1)

    print(f"Coletados {len(repositories)} repositórios (brutos)")
    return repositories

# Função para gerenciar o rate limit da API do GitHub. 
def waitIfRateLimited(rate_info: dict):
    if not rate_info:
        return
    remaining = rate_info.get("remaining")
    reset_at = rate_info.get("resetAt")
    if remaining is None or reset_at is None:
        return
    # Se estiver com menos de 10 requests restantes, aguarda até o reset
    if remaining < 10:
        reset_dt = datetime.fromisoformat(reset_at.replace('Z', '+00:00'))
        now = datetime.now(timezone.utc)
        wait_seconds = (reset_dt - now).total_seconds()
        if wait_seconds > 0:
            print(f"Rate limit baixo ({remaining} restantes). Aguardando {int(wait_seconds)+5}s até reset...")
            time.sleep(wait_seconds + 5)

# Função para filtrar os repositórios com totalCount >= MIN_PR_COUNT
def getRepoPrCount(owner: str, name: str) -> int:
    variables = {"owner": owner, "name": name}
    resp = executeGraphqlQuery(REPO_PR_COUNT_QUERY, variables)
    if not resp or "data" not in resp or not resp["data"].get("repository"):
        return 0
    rate_info = resp["data"].get("rateLimit")
    waitIfRateLimited(rate_info)
    return resp["data"]["repository"]["pullRequests"]["totalCount"]
    # Obtém a contagem total de pull requests para um repositório específico.