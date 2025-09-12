## `README.md` (para `laboratorio2/`)
# Laboratório 02 — Medição e Experimentação de Software

## Sprint 01 (S01)

Entrega:  
- Lista dos 1.000 repositórios Java (CSV)  
- Script(s) de automação: clone e execução do CK  
- Resultado das medições de 1 repositório (CSV)  

---

## 1. Preparação do Ambiente

### 1.1. Python (Ubuntu 20.04)  
No nível raiz do repositório `laboratorio2/`:

```bash
# Atualizar pacotes e instalar suporte a venv
sudo apt update
sudo apt install -y python3-venv

# Criar e ativar ambiente virtual
python3 -m venv .venv
source .venv/bin/activate

# Instalar dependências Python
pip install -r requirements.txt
````

### 1.2. Java

* Java 11 ou 17 instalado (usamos 17 no CK).
* Verifique com:

```bash
java -version
```

---

## 3. Scripts de Automação

### 3.1. Clonar um repositório Java

**Nível:** `laboratorio2/`

```bash
./scripts/clone_java_repos.sh apache commons-lang
```

Isso cria a pasta:

```
repos/apache__commons-lang
```

### 3.2. Executar CK em um repositório

**Nível:** `laboratorio2/`

```bash
./scripts/run_ck_one.sh repos/apache__commons-lang
```

Saída esperada:

```
data/raw/apache__commons-lang/class.csv
data/raw/apache__commons-lang/method.csv
data/raw/apache__commons-lang/field.csv
data/raw/apache__commons-lang/variable.csv
```

### 3.3. Gerar resumo das métricas

**Nível:** `laboratorio2/`

```bash
python src/python/summarize_ck.py \
  data/raw/apache__commons-lang \
  data/processed/ck_summary.csv
```

Saída esperada (`data/processed/ck_summary.csv`):

```csv
repo,cbo_mean,cbo_median,cbo_std,dit_mean,dit_median,dit_std,lcom_mean,lcom_median,lcom_std,loc_mean,loc_median,loc_std
apache__commons-lang,3.34,2.0,4.68,1.54,1.0,1.01,268.71,0.0,2955.71,80.70,15.0,269.47
```

---

## 4. Arquivos da Entrega (S01)

1. `data/github_top_1000_java_repositories.csv`
   Lista dos 1.000 repositórios Java (coletados via API do GitHub).
2. `scripts/clone_java_repos.sh`
   Script de automação de clonagem.
3. `scripts/run_ck_one.sh`
   Script de execução do CK.
4. `data/raw/apache__commons-lang/*`
   Arquivos CSV do CK de 1 repositório.
5. `data/processed/ck_summary.csv`
   Resumo das métricas do repositório processado.

---
