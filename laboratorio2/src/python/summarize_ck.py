import sys
import pandas as pd
from pathlib import Path

def find_col(cols, candidates):
    low = {c.lower(): c for c in cols}
    for cand in candidates:
        if cand.lower() in low:
            return low[cand.lower()]
    return None


def summarize_repo(input_dir: Path, out_csv: Path = None):
    class_csv = input_dir / "class.csv"
    if not class_csv.exists():
        raise FileNotFoundError(f"class.csv não encontrado em {input_dir}")

    df = pd.read_csv(class_csv)

    # mapeia nomes possíveis nas versões do CK
    col_map = {
        "cbo":       find_col(df.columns, ["cbo"]),
        "dit":       find_col(df.columns, ["dit"]),
        "lcom":      find_col(df.columns, ["lcom", "lcom*"]),
        "loc":       find_col(df.columns, ["loc", "locclass"]),
        "comments":  find_col(df.columns, ["locComments", "loccomments"]),  # NOVO
    }

    stats = {"repo": input_dir.name}
    for key, col in col_map.items():
        if col and col in df.columns:
            s = pd.to_numeric(df[col], errors="coerce")
            stats[f"{key}_mean"]   = float(s.mean())
            stats[f"{key}_median"] = float(s.median())
            stats[f"{key}_std"]    = float(s.std())
        else:
            stats[f"{key}_mean"] = stats[f"{key}_median"] = stats[f"{key}_std"] = None

    if out_csv is not None:
        out_csv = Path(out_csv)
        out_csv.parent.mkdir(parents=True, exist_ok=True)
        pd.DataFrame([stats]).to_csv(out_csv, index=False)
        print(f"✓ Resumo salvo em {out_csv}")
    return stats

if __name__ == "__main__":
    if len(sys.argv) != 3:
        print("Uso: python src/python/summarize_ck.py <data/raw/owner__name> <data/processed/ck_summary.csv>")
        sys.exit(1)
    summarize_repo(Path(sys.argv[1]), Path(sys.argv[2]))
