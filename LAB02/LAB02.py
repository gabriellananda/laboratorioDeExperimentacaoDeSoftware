import requests
import json
import csv
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
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

#Headers para autenticação
HEADERS = {
    "Authorization": f"Bearer {GITHUB_TOKEN}",
    "Content-Type": "application/json"
}