import os, sqlite3, json, hashlib
import pandas as pd

DEFAULT_DB_PATH = os.environ.get("DB_PATH", os.path.join("data", "cfd.db"))

DDL = """
CREATE TABLE IF NOT EXISTS resultados (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    L_m REAL,
    Malha TEXT,
    h REAL,
    Tempo_Execucao TEXT,
    Tempo_Execucao_min REAL,
    Tempo_Execucao_h REAL,
    CL_Asa_Stab REAL,
    source_filename TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    row_hash TEXT UNIQUE
);
"""

def get_conn(db_path: str = DEFAULT_DB_PATH):
    os.makedirs(os.path.dirname(db_path), exist_ok=True)
    conn = sqlite3.connect(db_path, check_same_thread=False)
    conn.execute(DDL)
    return conn

def compute_row_hash(row: dict) -> str:
    key = json.dumps({
        "L_m": row.get("L_m"),
        "Malha": row.get("Malha"),
        "h": row.get("h"),
        "Tempo_Execucao": row.get("Tempo_Execucao"),
        "CL_Asa_Stab": row.get("CL_Asa_Stab")
    }, sort_keys=True)
    return hashlib.sha256(key.encode("utf-8")).hexdigest()

def upsert_rows(rows: list[dict], db_path: str = DEFAULT_DB_PATH) -> tuple[int, int]:
    conn = get_conn(db_path)
    cur = conn.cursor()
    inserted = 0
    skipped = 0
    for r in rows:
        rh = compute_row_hash(r)
        try:
            cur.execute(
                """
                INSERT INTO resultados
                (L_m, Malha, h, Tempo_Execucao, Tempo_Execucao_min, Tempo_Execucao_h,
                 CL_Asa_Stab, source_filename, row_hash)
                VALUES (?,?,?,?,?,?,?,?,?)
                """,
                (
                    r.get("L_m"),
                    r.get("Malha"),
                    r.get("h"),
                    r.get("Tempo_Execucao"),
                    r.get("Tempo_Execucao_min"),
                    r.get("Tempo_Execucao_h"),
                    r.get("CL_Asa_Stab"),
                    r.get("source_filename"),
                    rh,
                )
            )
            inserted += 1
        except sqlite3.IntegrityError:
            skipped += 1
    conn.commit()
    conn.close()
    return inserted, skipped

def fetch_dataframe(db_path: str = DEFAULT_DB_PATH) -> pd.DataFrame:
    conn = get_conn(db_path)
    df = pd.read_sql_query("SELECT L_m, Malha, h, Tempo_Execucao, Tempo_Execucao_min, Tempo_Execucao_h, CL_Asa_Stab, source_filename, created_at FROM resultados ORDER BY L_m ASC", conn)
    conn.close()
    return df

def export_csv(path: str, db_path: str = DEFAULT_DB_PATH) -> str:
    df = fetch_dataframe(db_path)
    df.to_csv(path, index=False, encoding="utf-8")
    return path
