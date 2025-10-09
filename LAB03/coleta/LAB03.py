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
SEARCH_REPOS_QUERY = '''query($first: Int!, $after: String) {
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
PULLS_PAGE_QUERY ='''
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

# Função para coletar PRs paginados de um repositório e filtrar por critérios do enunciado
def collectPrsForRepo(owner: str, name: str) -> List[dict]:
    prs = []
    cursor = None
    page_size = 50
    fetched_pages = 0

    while True:
        variables = {"owner": owner, "name": name, "first": page_size, "after": cursor}
        resp = executeGraphqlQuery(PULLS_PAGE_QUERY, variables)
        if not resp or "data" not in resp:
            break
        rate_info = resp["data"].get("rateLimit")
        waitIfRateLimited(rate_info)

        pulls = resp["data"]["repository"]["pullRequests"]
        nodes = pulls["nodes"]

        for pr in nodes:
            # Extrair timestamps
            created_at = parseIso(pr.get("createdAt"))
            closed_at = parseIso(pr.get("closedAt"))
            merged_at = parseIso(pr.get("mergedAt"))

            # Determinar status final
            status = "MERGED" if merged_at is not None else "CLOSED"
            final_time = merged_at if merged_at is not None else closed_at
            if final_time is None:
                # pular PRs sem fechamento
                continue

            duration_s = (final_time - created_at).total_seconds()

            # Requisitos do enunciado:
            # - reviews.totalCount >= 1
            # - duration > 1 hora
            reviews_total = safeInt(pr.get("reviews", {}).get("totalCount"))
            if reviews_total < 1:
                continue
            if duration_s <= MIN_PR_DURATION_SECONDS:
                continue

            # Métricas solicitadas
            pr_record = {
                "repo_owner": owner,
                "repo_name": name,
                "pr_number": pr.get("number"),
                "pr_title": pr.get("title"),
                "pr_url": pr.get("url"),
                "status": status,
                "createdAt": pr.get("createdAt"),
                "closedAt": pr.get("closedAt"),
                "mergedAt": pr.get("mergedAt"),
                "time_to_close_seconds": int(duration_s),
                "additions": safeInt(pr.get("additions")),
                "deletions": safeInt(pr.get("deletions")),
                "changed_files": safeInt(pr.get("changedFiles")),
                "description_length": len(pr.get("bodyText") or ""),
                "reviews_count": reviews_total,
                "comments_count": safeInt(pr.get("comments", {}).get("totalCount")),
                "participants_count": safeInt(pr.get("participants", {}).get("totalCount")),
                "author": (pr.get("author") or {}).get("login")
            }
            prs.append(pr_record)

        # paginação
        page_info = pulls.get("pageInfo")
        if not page_info or not page_info.get("hasNextPage"):
            break
        cursor = page_info.get("endCursor")
        fetched_pages += 1
        # pequeno delay para polidez
        time.sleep(1)

    return prs

# Funções utilitárias
# Converte uma string de data e hora para um objeto `datetime` com informações de fuso horário UTC.
def parseIso(s: Optional[str]) -> Optional[datetime]:
    if not s:
        return None
    try:
        return datetime.fromisoformat(s.replace('Z', '+00:00')).astimezone(timezone.utc)
    except Exception:
        return None

# Converte um valor para um número inteiro de forma segura. Retorna 0 se o valor for `None` ou se ocorrer um erro na conversão.
def safeInt(value) -> int:
    try:
        return int(value) if value is not None else 0
    except Exception:
        return 0

def main():

    # Busca e filtra repositórios com um número mínimo de PRs.
    top_repos = getTopRepositories(TOP_REPOS_LIMIT)
    
    print("\nFiltrando repositórios com pelo menos {} PRs (OPEN+CLOSED+MERGED)...".format(MIN_PR_COUNT))
    selected_repos = []
    for i, r in enumerate(top_repos, start=1):
        owner = r["owner"]["login"]
        name = r["name"]
        print(f"[{i}/{len(top_repos)}] Checando {owner}/{name}...", end=' ')
        pr_count = getRepoPrCount(owner, name)
        print(f"{pr_count} PRs")
        if pr_count >= MIN_PR_COUNT:
            selected_repos.append({
                "owner": owner,
                "name": name,
                "url": r.get("url"),
                "stars": r.get("stargazerCount"),
                "pr_count": pr_count
            })
        # curto delay
        time.sleep(0.5)

# Salva a lista de repositórios selecionados em um arquivo CSV.
    print(f"\n✓ {len(selected_repos)} repositórios passaram no filtro (>= {MIN_PR_COUNT} PRs). Salvando {REPOS_CSV}...")
    with open(REPOS_CSV, "w", newline='', encoding='utf-8') as f:
        writer = csv.DictWriter(f, fieldnames=["owner", "name", "url", "stars", "pr_count"])
        writer.writeheader()
        for rr in selected_repos:
            writer.writerow(rr)


    # Para cada repositório selecionado, coletar PRs e aplicar filtros de PR. Salvar os dados em um CSV.
    all_prs = []
    for j, rr in enumerate(selected_repos, start=1):
        owner = rr["owner"]
        name = rr["name"]
        print(f"\n[{j}/{len(selected_repos)}] Coletando PRs de {owner}/{name}...")
        prs = collectPrsForRepo(owner, name)
        print(f"  -> {len(prs)} PRs após aplicar filtros (reviews>=1 e duração>1h)")
        all_prs.extend(prs)
        # salvo parcial para evitar perda se demorar demais
        with open(PRS_CSV, "w", newline='', encoding='utf-8') as f:
            fieldnames = [
                "repo_owner","repo_name","pr_number","pr_title","pr_url","status",
                "createdAt","closedAt","mergedAt","time_to_close_seconds",
                "additions","deletions","changed_files","description_length",
                "reviews_count","comments_count","participants_count","author"
            ]
            writer = csv.DictWriter(f, fieldnames=fieldnames)
            writer.writeheader()
            for p in all_prs:
                writer.writerow(p)

    print(f"\n✓ Coleta finalizada. Total de PRs coletados: {len(all_prs)}")
    print(f"Arquivos gerados: {REPOS_CSV}, {PRS_CSV}")

if __name__ == '__main__':
    main()