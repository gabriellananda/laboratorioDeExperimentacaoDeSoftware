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