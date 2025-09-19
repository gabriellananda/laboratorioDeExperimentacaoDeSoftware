import requests
import json
import csv
from datetime import datetime, timezone
import time
import warnings
import os
import subprocess
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns

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

#Execução Principal
if __name__ == "__main__":
    repositories = getBasicRepositories(1000)
    final_data = []

    for i, repo in enumerate(repositories, start=1):
        print(f"\n[{i}/{len(repositories)}] Processando {repo['owner']['login']}/{repo['name']}")

        # 1) Métricas de atividade
        heavy = getHeavyMetrics(repo['owner']['login'], repo['name'])
        time.sleep(1)  # para não estourar rate limit

        # 2) Clonar e contar LOC
        repo_path = cloneRepository(repo['url'], CLONE_DIR)
        if repo_path:
            loc, comments = countJavaLOC(repo_path)
            # Excluir repositório clonado após contagem
            subprocess.run(["rm", "-rf", repo_path], check=True)
        else:
            loc, comments = 0, 0

        # 3) Adicionar dados ao CSV
        final_data.append({
            "name": repo["name"],
            "owner": repo["owner"]["login"],
            "url": repo["url"],
            "stars": repo["stargazerCount"],
            "createdAt": repo["createdAt"],
            "updatedAt": repo["updatedAt"],
            "merged_pull_requests": heavy["merged_pull_requests"],
            "releases": heavy["releases"],
            "loc": loc,
            "comment_lines": comments
        })

    # Salvar CSV final com as métricas de processo
    csv_filename = "github_java_repositories_full_metrics.csv"
    with open(csv_filename, "w", newline="", encoding="utf-8") as csvfile:
        fieldnames = ["name", "owner", "url", "stars", "createdAt", "updatedAt",
                      "merged_pull_requests", "releases", "loc", "comment_lines"]
        writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
        writer.writeheader()
        for row in final_data:
            writer.writerow(row)

    print(f"\n✓ Todas as métricas salvas em {csv_filename}")

# Análise Estatística
df = pd.read_csv(csv_filename)

if not df.empty:
    # Padronizar para UTC (evita erro tz-aware vs tz-naive)
    df['createdAt'] = pd.to_datetime(df['createdAt'], utc=True)
    df['updatedAt'] = pd.to_datetime(df['updatedAt'], utc=True)

    # Usar datetime.now(timezone.utc) para manter consistência
    now = datetime.now(timezone.utc)

    # Calcula idade do repositório (anos) e dias desde última atualização
    df['repo_age_years'] = (now - df['createdAt']).dt.days / 365
    df['days_since_last_update'] = (now - df['updatedAt']).dt.days

    print("\n=== ANÁLISE ESTATÍSTICA DETALHADA ===")

    # Métricas descritivas
    print("\n1. MÉTRICAS DESCRITIVAS:")
    print(df[['stars', 'repo_age_years', 'merged_pull_requests',
              'releases', 'loc', 'comment_lines']].describe())

    # Correlação entre métricas
    print("\n2. CORRELAÇÕES ENTRE MÉTRICAS:")
    print(df[['stars', 'repo_age_years', 'merged_pull_requests',
              'releases', 'loc', 'comment_lines']].corr().round(3))

    # Repositórios ativos nos últimos 30 dias
    print("\n3. REPOSITÓRIOS MAIS ATIVOS (últimos 30 dias):")
    active_repos = df[df['days_since_last_update'] <= 30]
    print(f"   • {len(active_repos)} repositórios ({len(active_repos)/len(df)*100:.1f}%)")

    # Visualizações
    plt.style.use('default')
    sns.set_palette("husl")
    fig = plt.figure(figsize=(20, 20))

    # Distribuição da idade dos repositórios
    plt.subplot(3, 2, 1)
    plt.hist(df['repo_age_years'], bins=30, alpha=0.7, color='skyblue', edgecolor='black')
    plt.title('Distribuição da Idade dos Repositórios')
    plt.xlabel('Idade (anos)')
    plt.ylabel('Frequência')
    plt.grid(True, alpha=0.3)

    # Distribuição de estrelas
    plt.subplot(3, 2, 2)
    stars_data = df['stars']
    stars_95th = stars_data.quantile(0.95)
    plt.hist(stars_data[stars_data <= stars_95th], bins=30, alpha=0.7, color='orange', edgecolor='black')
    plt.title('Distribuição de Estrelas (Popularidade)')
    plt.xlabel('Estrelas')
    plt.ylabel('Frequência')
    plt.grid(True, alpha=0.3)

    # Distribuição de releases 
    plt.subplot(3, 2, 3)
    releases_data = df['releases']
    releases_95th = releases_data.quantile(0.95)
    plt.hist(releases_data[releases_data <= releases_95th], bins=30, alpha=0.7, color='lightgreen', edgecolor='black')
    plt.title('Distribuição de Releases')
    plt.xlabel('Número de Releases')
    plt.ylabel('Frequência')
    plt.grid(True, alpha=0.3)

    # Distribuição de PRs aceitas 
    plt.subplot(3, 2, 4)
    pr_data = df['merged_pull_requests']
    pr_95th = pr_data.quantile(0.95)
    plt.hist(pr_data[pr_data <= pr_95th], bins=30, alpha=0.7, color='pink', edgecolor='black')
    plt.title('Distribuição de Pull Requests Aceitas')
    plt.xlabel('Número de PRs')
    plt.ylabel('Frequência')
    plt.grid(True, alpha=0.3)

    # Distribuição de linhas de código (LOC) 
    plt.subplot(3, 2, 5)
    loc_data = df['loc']
    loc_95th = loc_data.quantile(0.95)
    plt.hist(loc_data[loc_data <= loc_95th], bins=30, alpha=0.7, color='purple', edgecolor='black')
    plt.title('Distribuição de Linhas de Código (LOC)')
    plt.xlabel('LOC')
    plt.ylabel('Frequência')
    plt.grid(True, alpha=0.3)

    # Relação Idade vs Estrelas
    plt.subplot(3, 2, 6)
    plt.scatter(df['repo_age_years'], df['stars'], alpha=0.6, color='brown')
    plt.title('Idade vs Estrelas')
    plt.xlabel('Idade (anos)')
    plt.ylabel('Estrelas')
    plt.grid(True, alpha=0.3)

    # Ajusta layout e salva gráfico
    plt.tight_layout()
    plt.savefig('github_java_repositories_analysis.png', dpi=300, bbox_inches='tight')
    plt.show()

    print("\n✓ Análise completa finalizada!")
    print("✓ Gráficos salvos como 'github_java_repositories_analysis.png'")

else:
    print("✗ Não foi possível realizar a análise - dados não disponíveis")