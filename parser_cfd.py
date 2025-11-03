import re

PADRAO_REGEX = r'^(result\d+)_(.*?)_L(\d+\.\d+)m_malha_(\d+x\d+)_h(\d+\.\d+)_(.*)min$'
REGEX_COMPILADO = re.compile(PADRAO_REGEX)

def tempo_str_para_minutos(s: str) -> float | None:
    if s is None:
        return None
    txt = str(s).strip().lower()
    m = re.fullmatch(r"\s*(\d+)\s*h\s*(\d+)?\s*(?:min)?\s*", txt)
    if m:
        horas = int(m.group(1)); mins = int(m.group(2)) if m.group(2) else 0
        return float(horas * 60 + mins)
    txt = re.sub(r"(mins?|minutes?)$", "", txt)
    txt = txt.replace("_", ".").replace(",", ".")
    txt = re.sub(r"[^0-9.]+", "", txt)
    try:
        return float(txt)
    except Exception:
        return None

def parse_from_filename(filename_no_ext: str):
    m = REGEX_COMPILADO.match(filename_no_ext)
    if not m:
        return None
    try:
        L_m = float(m.group(3))
        malha = m.group(4)
        h = float(m.group(5))
        tempo_exec = m.group(6) + "min"
        return {"L_m": L_m, "Malha": malha, "h": h, "Tempo_Execucao": tempo_exec}
    except Exception:
        return None

def parse_from_text(content: str):
    cl_asa = None
    cl_stab = None
    for raw in content.splitlines():
        linha = raw.strip()
        if linha.startswith("Asa_right"):
            partes = linha.split(",")
            if len(partes) > 4:
                try: cl_asa = float(partes[4])
                except: pass
        elif linha.startswith("Stab_direita"):
            partes = linha.split(",")
            if len(partes) > 4:
                try: cl_stab = float(partes[4])
                except: pass
    if cl_asa is None or cl_stab is None:
        return None
    return {"CL_Asa_Stab": cl_asa + cl_stab}

def parse_uploaded_txt(filename: str, bytes_data: bytes):
    base = filename.rsplit(".", 1)[0]
    meta = parse_from_filename(base)
    if not meta:
        return None
    try:
        content = bytes_data.decode("utf-8", errors="ignore")
    except Exception:
        return None
    vals = parse_from_text(content)
    if not vals:
        return None
    row = {**meta, **vals}
    row["Tempo_Execucao_min"] = tempo_str_para_minutos(row["Tempo_Execucao"])
    row["Tempo_Execucao_h"] = (row["Tempo_Execucao_min"] / 60.0) if row["Tempo_Execucao_min"] is not None else None
    return row
