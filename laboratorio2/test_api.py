import os, requests
from dotenv import load_dotenv

load_dotenv()  # carrega o .env
token = os.getenv("GITHUB_TOKEN")

if not token:
    raise RuntimeError("⚠️  GITHUB_TOKEN não encontrado no .env")

url = "https://api.github.com/graphql"
query = "{ viewer { login } }"

resp = requests.post(
    url,
    json={"query": query},
    headers={"Authorization": f"Bearer {token}"}
)

print(resp.json())
