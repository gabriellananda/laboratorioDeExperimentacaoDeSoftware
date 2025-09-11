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