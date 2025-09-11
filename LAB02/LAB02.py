import requests
import json
import csv
from datetime import datetime, timezone
import time
import warnings
import os
import subprocess

warnings.filterwarnings('ignore')

#Configurações do token
GITHUB_TOKEN = ""  # <<< coloque seu token aqui

#URL da API GraphQL do Github
GRAPHQL_URL = "https://api.github.com/graphql"

#Pasta onde os repositórios serão clonados
CLONE_DIR = "cloned_repos"

#Headers para autenticação
HEADERS = {
    "Authorization": f"Bearer {GITHUB_TOKEN}",
    "Content-Type": "application/json"
}

# Queries GraphQL
BASIC_REPOS_QUERY = """
query($first: Int!, $after: String) {
  search(query: "language:Java stars:>1 sort:stars-desc", type: REPOSITORY, first: $first, after: $after) {
    pageInfo {
      hasNextPage
      endCursor
    }
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
  rateLimit {
    remaining
    resetAt
  }
}
"""

HEAVY_METRICS_QUERY = """
query($owner: String!, $name: String!) {
  repository(owner: $owner, name: $name) {
    pullRequests(states: [MERGED]) { totalCount }
    releases { totalCount }
  }
}
"""

#Função para executar consultas
def executeGraphqlQuery(query, variables=None):
    payload = {
        "query": query,
        "variables": variables or {}
    }
    response = requests.post(GRAPHQL_URL, headers=HEADERS, json=payload)

    if response.status_code == 200:
        result = response.json()
        if "errors" in result:
            print(f"GraphQL Errors: {result['errors']}")
            return None
        return result
    else:
        print(f"HTTP Error {response.status_code}: {response.text}")
        return None

#Função para pegar repositórios básicos
def getBasicRepositories(limit=100):
    repositories = []
    cursor = None
    fetched = 0

    print(f"Buscando informações básicas de {limit} repositórios Java...")
    while fetched < limit:
        remaining_to_fetch = min(100, limit - fetched)
        variables = {"first": remaining_to_fetch, "after": cursor}
        result = executeGraphqlQuery(BASIC_REPOS_QUERY, variables)
        if not result or "data" not in result:
            print("Erro ao buscar repositórios")
            break

        # Verificar rate limit
        rate_limit = result["data"]["rateLimit"]
        print(f"Rate limit remaining: {rate_limit['remaining']}")
        if rate_limit["remaining"] < 10:
            reset_time = datetime.fromisoformat(rate_limit["resetAt"].replace('Z', '+00:00'))
            wait_time = (reset_time - datetime.now(timezone.utc)).total_seconds()
            if wait_time > 0:
                print(f"Rate limit baixo. Aguardando {wait_time:.0f} segundos...")
                time.sleep(wait_time + 5)

        search_data = result["data"]["search"]
        repos = search_data["nodes"]
        repositories.extend(repos)
        fetched += len(repos)

        # Verificar se há mais páginas
        if not search_data["pageInfo"]["hasNextPage"] or fetched >= limit:
            break
        cursor = search_data["pageInfo"]["endCursor"]
        time.sleep(1)  # Pausa entre requisições

    print(f"✓ Coletados {len(repositories)} repositórios com informações básicas")
    return repositories

#Função para pegar métricas detalhadas
def getHeavyMetrics(owner, name):
    variables = {"owner": owner, "name": name}
    result = executeGraphqlQuery(HEAVY_METRICS_QUERY, variables)
    if not result or "data" not in result or not result["data"]["repository"]:
        return {"merged_pull_requests": 0, "releases": 0}
    repo_data = result["data"]["repository"]
    return {
        "merged_pull_requests": repo_data["pullRequests"]["totalCount"],
        "releases": repo_data["releases"]["totalCount"]
    }