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

def cloneRepository(url, dest_folder):
    repo_name = url.split("/")[-1]
    repo_path = os.path.join(dest_folder, repo_name)
    if not os.path.exists(dest_folder):
        os.makedirs(dest_folder)
    if os.path.exists(repo_path):
        print(f"Repositório {repo_name} já clonado.")
        return repo_path
    try:
        subprocess.run(["git", "clone", "--depth", "1", url, repo_path], check=True)
        return repo_path
    except subprocess.CalledProcessError:
        print(f"Erro ao clonar {url}")
        return None

def countJavaLOC(repo_path):
    loc = 0
    comment_lines = 0
    for root, dirs, files in os.walk(repo_path):
        for file in files:
            if file.endswith(".java"):
                file_path = os.path.join(root, file)
                with open(file_path, "r", encoding="utf-8", errors="ignore") as f:
                    in_block_comment = False
                    for line in f:
                        line_strip = line.strip()
                        if in_block_comment:
                            comment_lines += 1
                            if "*/" in line_strip:
                                in_block_comment = False
                            continue
                        if line_strip.startswith("/*"):
                            comment_lines += 1
                            in_block_comment = True
                        elif line_strip.startswith("//"):
                            comment_lines += 1
                        elif line_strip != "":
                            loc += 1
    return loc, comment_lines