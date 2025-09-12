# src/python/collect_repos.py
import os
import time
import csv
import requests
from datetime import datetime, timezone
from dotenv import load_dotenv

load_dotenv()  # carrega .env na raiz do projeto

# === CONFIG ===
GITHUB_TOKEN = os.getenv("GITHUB_TOKEN")
if not GITHUB_TOKEN:
    raise RuntimeError("GITHUB_TOKEN não definido. Crie um .env na raiz com GITHUB_TOKEN=...")

GRAPHQL_URL = "https://api.github.com/graphql"
HEADERS = {
    "Authorization": f"Bearer {GITHUB_TOKEN}",
    "Content-Type": "application/json"
}

# === QUERIES GRAPHQL ===
BASIC_REPOS_QUERY = """
query($first: Int!, $after: String) {
  search(query: "language:Java stars:>1 sort:stars-desc", type: REPOSITORY, first: $first, after: $after) {
    pageInfo { hasNextPage endCursor }
    nodes {
      ... on Repository {
        id
        name
        owner { login }
        url
        stargazerCount
        createdAt
        updatedAt
        primaryLanguage { name }
        forkCount
        watchers { totalCount }
        description
      }
    }
  }
  rateLimit { remaining resetAt }
}
"""

def execute_graphql_query(query: str, variables: dict | None = None):
    payload = {"query": query, "variables": variables or {}}
    resp = requests.post(GRAPHQL_URL, headers=HEADERS, json=payload, timeout=30)
    if resp.status_code != 200:
        print(f"[HTTP {resp.status_code}] {resp.text[:200]}")
        return None
    data = resp.json()
    if "errors" in data:
        print(f"[GraphQL Errors] {data['errors']}")
        return None
    return data

def get_basic_repositories(limit=1000):
    repositories = []
    cursor = None
    fetched = 0

    print(f"→ Buscando informações básicas de {limit} repositórios Java...")
    while fetched < limit:
        remaining_to_fetch = min(100, limit - fetched)
        variables = {"first": remaining_to_fetch, "after": cursor}
        result = execute_graphql_query(BASIC_REPOS_QUERY, variables)

        if not result or "data" not in result:
            print("✗ Erro ao buscar repositórios (resposta vazia ou inválida)")
            break

        search_data = result["data"]["search"]
        repos = search_data["nodes"] or []
        repositories.extend(repos)
        fetched += len(repos)

        # rate limit (apenas log aqui; se quiser, pode dormir quando estiver baixo)
        rl = result["data"].get("rateLimit", {})
        if rl:
            print(f"   rateLimit.remaining={rl.get('remaining')} resetAt={rl.get('resetAt')}")

        if not search_data["pageInfo"]["hasNextPage"] or fetched >= limit:
            break

        cursor = search_data["pageInfo"]["endCursor"]
        time.sleep(1)  # educado com a API

    print(f"✓ Coletados {len(repositories)} repositórios")
    return repositories

def save_repos_csv(repositories, csv_filename="data/processed/github_top_1000_java_repositories.csv"):
    os.makedirs(os.path.dirname(csv_filename), exist_ok=True)
    with open(csv_filename, "w", newline="", encoding="utf-8") as csvfile:
        fieldnames = ["name", "owner", "url", "stars", "createdAt", "updatedAt"]
        writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
        writer.writeheader()
        for repo in repositories:
            writer.writerow({
                "name": repo["name"],
                "owner": repo["owner"]["login"],
                "url": repo["url"],
                "stars": repo["stargazerCount"],
                "createdAt": repo["createdAt"],
                "updatedAt": repo["updatedAt"],
            })
    print(f"✓ Lista salva em {csv_filename}")

if __name__ == "__main__":
    repos = get_basic_repositories(1000)
    if repos:
        save_repos_csv(repos)
    else:
        print("✗ Nenhum repositório coletado.")
