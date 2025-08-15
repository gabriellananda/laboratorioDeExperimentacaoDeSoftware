import requests
import json
import csv
import pandas as pd #usada para organizar, manipular e analisar dados.
import matplotlib.pyplot as plt #biblioteca de gráficos
import seaborn as sns #biblioteca de gráficos
from datetime import datetime, timezone
import time
import warnings
warnings.filterwarnings('ignore')

# Configuração do token
GITHUB_TOKEN = "SEU_TOKEN"

# Headers para autenticação
HEADERS = {
    "Authorization": f"Bearer {GITHUB_TOKEN}",
    "Content-Type": "application/json"
}

# URL da API GraphQL do GitHub
GRAPHQL_URL = "https://api.github.com/graphql"

# Query 1: Informações básicas dos repositórios (leve)
BASIC_REPOS_QUERY = """
query($first: Int!, $after: String) {
  search(query: "stars:>1 sort:stars-desc", type: REPOSITORY, first: $first, after: $after) {
    pageInfo {
      hasNextPage
      endCursor
    }
    nodes {
      ... on Repository {
        id
        name
        owner {
          login
        }
        url
        stargazerCount
        createdAt
        updatedAt
        primaryLanguage {
          name
        }
        forkCount
        watchers {
          totalCount
        }
        description
      }
    }
  }
  rateLimit {
    remaining
    resetAt
  }
}
"""

# Query 2: Métricas pesadas para repositórios específicos
HEAVY_METRICS_QUERY = """
query($owner: String!, $name: String!) {
  repository(owner: $owner, name: $name) {
    pullRequests(states: [MERGED]) {
      totalCount
    }
    releases {
      totalCount
    }
    issues {
      totalCount
    }
    closedIssues: issues(states: [CLOSED]) {
      totalCount
    }
  }
  rateLimit {
    remaining
    resetAt
  }
}
"""

#Função para executar consultas
def executeGraphqlQuery(query, variables=None):

    #Executa uma query GraphQL na API do GitHub
    #Argumentos: query (str): Query GraphQL | variables (dict): Variáveis para a query
    #Retornos: dict: Resposta da API

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

    #Busca informações básicas dos repositórios mais populares
    #Argumentos: limit (int): Número de repositórios para buscar
    #Retornos: list: Lista de repositórios com informações básicas
    
    repositories = []
    cursor = None
    fetched = 0

    print(f"Buscando informações básicas de {limit} repositórios...")

    while fetched < limit:
        remaining_to_fetch = min(100, limit - fetched)

        variables = {
            "first": remaining_to_fetch,
            "after": cursor
        }

        print(f"Fetching repositories {fetched + 1} to {fetched + remaining_to_fetch}...")

        result = executeGraphqlQuery(BASIC_REPOS_QUERY, variables)

        if not result or "data" not in result:
            print("Erro ao buscar repositórios")
            break

        search_data = result["data"]["search"]
        repos = search_data["nodes"]

        repositories.extend(repos)
        fetched += len(repos)

        # Verificar rate limit
        rate_limit = result["data"]["rateLimit"]
        print(f"Rate limit remaining: {rate_limit['remaining']}")

        if rate_limit["remaining"] < 10:
            reset_time = datetime.fromisoformat(rate_limit["resetAt"].replace('Z', '+00:00'))
            wait_time = (reset_time - datetime.now(timezone.utc)).total_seconds()
            if wait_time > 0:
                print(f"Rate limit baixo. Aguardando {wait_time:.0f} segundos...")
                time.sleep(wait_time + 5)

        # Verificar se há mais páginas
        if not search_data["pageInfo"]["hasNextPage"] or fetched >= limit:
            break

        cursor = search_data["pageInfo"]["endCursor"]
        time.sleep(1)  # Pausa entre requisições

    print(f"Coletados {len(repositories)} repositórios com informações básicas")
    return repositories

#Função para pegar métricas detalhadas
def getHeavyMetrics(owner, name):

    #Busca métricas pesadas para um repositório específico
    #Argumentos: owner (str): Proprietário do repositório | name (str): Nome do repositório
    #Retornos: dict: Métricas pesadas do repositório
    
    variables = {
        "owner": owner,
        "name": name
    }

    #Executa a consulta pesada usando o dono e nome do repositório.
    result = executeGraphqlQuery(HEAVY_METRICS_QUERY, variables)

    if not result or "data" not in result or not result["data"]["repository"]:
        return {
            "merged_pull_requests": 0,
            "releases": 0,
            "total_issues": 0,
            "closed_issues": 0
        }

    repo_data = result["data"]["repository"]

    return {
        "merged_pull_requests": repo_data["pullRequests"]["totalCount"],
        "releases": repo_data["releases"]["totalCount"],
        "total_issues": repo_data["issues"]["totalCount"],
        "closed_issues": repo_data["closedIssues"]["totalCount"]
    }

#Função para calcular métricas
def calculateMetrics(repo_data, heavy_metrics):
  
    #Calcula as métricas solicitadas
    #Argumentos: repoData (dict): Dados básicos do repositório | heavyMetrics (dict): Métricas pesadas do repositório
    #Retornos: dict: Métricas calculadas

    # 1. Idade do repositório (em dias)
    created_at = datetime.fromisoformat(repo_data["createdAt"].replace('Z', '+00:00'))
    repo_age_days = (datetime.now(timezone.utc) - created_at).days

    # 2. Total de pull requests aceitas (merged)
    merged_prs = heavy_metrics["merged_pull_requests"]

    # 3. Total de releases
    total_releases = heavy_metrics["releases"]

    # 4. Tempo até a última atualização (em dias)
    updated_at = datetime.fromisoformat(repo_data["updatedAt"].replace('Z', '+00:00'))
    days_since_update = (datetime.now(timezone.utc) - updated_at).days

    # 5. Linguagem primária
    primary_language = repo_data["primaryLanguage"]["name"] if repo_data["primaryLanguage"] else "Unknown"

    # 6. Razão entre issues fechadas e total de issues
    total_issues = heavy_metrics["total_issues"]
    closed_issues = heavy_metrics["closed_issues"]
    closed_issues_ratio = closed_issues / total_issues if total_issues > 0 else 0

    return {
        "repo_age_days": repo_age_days,
        "merged_pull_requests": merged_prs,
        "total_releases": total_releases,
        "days_since_last_update": days_since_update,
        "primary_language": primary_language,
        "closed_issues_ratio": closed_issues_ratio,
        "total_issues": total_issues,
        "closed_issues": closed_issues
    }

# Teste com 100 repositórios com todas as métricas

print("\nTeste inicial com 100 repositórios (incluindo métricas pesadas):")

basic_repos_sample = getBasicRepositories(100)

if basic_repos_sample:
    print(f"✓ Informações básicas coletadas: {len(basic_repos_sample)} repositórios")

    # Coletar métricas pesadas para os primeiros 100 repositórios
    print("Coletando métricas pesadas para os 100 repositórios...")
    complete_repos_sample = []

    for i, repo in enumerate(basic_repos_sample):
        owner = repo["owner"]["login"]
        name = repo["name"]

        print(f"\nProcessando {i+1}/100: {owner}/{name}")

        # Buscar métricas pesadas
        heavy_metrics = getHeavyMetrics(owner, name)

        # Calcular métricas
        calculated_metrics = calculateMetrics(repo, heavy_metrics)

        # Imprimir todas as métricas obtidas
        print(f"  └─ Métricas:")
        print(f"     • Idade: {calculated_metrics['repo_age_days']} dias ({calculated_metrics['repo_age_days']/365:.1f} anos)")
        print(f"     • PRs aceitas: {calculated_metrics['merged_pull_requests']}")
        print(f"     • Releases: {calculated_metrics['total_releases']}")
        print(f"     • Dias desde última atualização: {calculated_metrics['days_since_last_update']}")
        print(f"     • Linguagem primária: {calculated_metrics['primary_language']}")
        print(f"     • Taxa de issues fechadas: {calculated_metrics['closed_issues_ratio']:.2%} ({calculated_metrics['closed_issues']}/{calculated_metrics['total_issues']})")

        # Combinar todos os dados
        complete_repo = {
            "name": name,
            "owner": owner,
            "url": repo["url"],
            "stars": repo["stargazerCount"],
            "forks": repo["forkCount"],
            "watchers": repo["watchers"]["totalCount"],
            "created_at": repo["createdAt"],
            "updated_at": repo["updatedAt"],
            "description": repo["description"] or "",
            **calculated_metrics
        }

        complete_repos_sample.append(complete_repo)

        # Pausa entre requisições para evitar rate limit
        if (i + 1) % 10 == 0:
            print(f"\n⏸ Pausa após {i+1} repositórios...")
            time.sleep(2)

    print(f"\n✓ Sucesso! Coletados {len(complete_repos_sample)} repositórios com todas as métricas")
else:
    print("✗ Erro na coleta de repositórios")