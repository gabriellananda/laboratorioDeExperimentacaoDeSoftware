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