import os
import time
import numpy as np
import pandas as pd
import streamlit as st

from parser_cfd import parse_uploaded_txt
from storage import upsert_rows, fetch_dataframe, export_csv, DEFAULT_DB_PATH
from charts import chart_cl_vs_L, chart_tempo_vs_L

# Configuração da página
st.set_page_config(page_title="CFD Post-Processing", page_icon="🌀", layout="wide")

st.title("🌀 Pós-processamento CFD – Upload incremental com persistência")
st.caption("Envie arquivos .txt de resultados; a base é atualizada de forma idempotente e os gráficos são re-renderizados.")

# Sidebar
with st.sidebar:
    st.header("Configuração")
    db_path = st.text_input("Caminho do banco (SQLite)", value=DEFAULT_DB_PATH)
    st.write(f"DB em: `{db_path}`")
    st.divider()
    st.markdown("**Ajuda**")
    st.write("• Persistência em SQLite com hash para evitar duplicatas.")
    st.write("• Nome do arquivo no padrão do pipeline; conteúdo com linhas `Asa_right` e `Stab_direita`.")

# Upload
st.subheader("Upload de arquivos")
files = st.file_uploader("Arraste e solte seus .txt", type=["txt"], accept_multiple_files=True)

if files:
    rows = []
    for up in files:
        data = up.read()
        row = parse_uploaded_txt(up.name, data)
        if row:
            row["source_filename"] = up.name
            rows.append(row)
            # Salvar o bruto (opcional)
            try:
                os.makedirs("uploads", exist_ok=True)
                with open(os.path.join("uploads", up.name), "wb") as f:
                    f.write(data)
            except Exception:
                pass

    if not rows:
        st.warning("Nenhum arquivo válido foi reconhecido.")
    else:
        ins, dup = upsert_rows(rows, db_path=db_path)
        st.success(f"Inseridos: {ins} | Ignorados (duplicados): {dup}")
        with st.expander("Prévia das linhas parseadas"):
            st.dataframe(pd.DataFrame(rows))

# Base
st.subheader("Base de dados")
df = fetch_dataframe(db_path=db_path)

if not df.empty:
    df["Malha"] = df["Malha"].astype(str)
    df["L_m"] = pd.to_numeric(df["L_m"], errors="coerce")

st.write(f"Total de pontos: **{len(df)}**")
st.dataframe(df, use_container_width=True)

# Gráficos (com filtros robustos)
st.subheader("Gráficos")
if len(df) > 0:
    col1, col2 = st.columns(2)

    with col1:
        malhas = sorted(df["Malha"].astype(str).unique().tolist())
        sel_malha = st.multiselect("Filtrar por Malha", options=malhas, default=malhas)

    with col2:
        l_values = pd.to_numeric(df["L_m"], errors="coerce").replace([np.inf, -np.inf], np.nan).dropna()
        if l_values.empty:
            st.warning("Não há valores numéricos válidos de L_m.")
            sel_L = (None, None)
        else:
            Lmin = float(l_values.min())
            Lmax = float(l_values.max())

            if np.isclose(Lmin, Lmax):
                st.info(f"Apenas um L_m disponível ({Lmin}). Filtro desativado.")
                sel_L = (Lmin, Lmax)
            else:
                spread = Lmax - Lmin
                step = max(round(spread / 100.0, 6), 1e-6)  # passo dinâmico seguro

                # Tenta o slider; se der ruim, fallback para select_slider
                try:
                    sel_L = st.slider(
                        "Filtrar por L_m",
                        min_value=Lmin, max_value=Lmax,
                        value=(Lmin, Lmax),
                        step=step,
                        format="%.6f",
                    )
                except Exception:
                    unique_sorted = sorted(set(float(x) for x in l_values))
                    sel_L = st.select_slider(
                        "Filtrar por L_m",
                        options=unique_sorted,
                        value=(unique_sorted[0], unique_sorted[-1]),
                    )

    # Aplica filtros
    if sel_L[0] is None:
        dff = df[df["Malha"].isin(sel_malha)].copy()
    else:
        dff = df[
            (df["Malha"].isin(sel_malha)) &
            (pd.to_numeric(df["L_m"], errors="coerce") >= sel_L[0]) &
            (pd.to_numeric(df["L_m"], errors="coerce") <= sel_L[1])
        ].copy()

    if dff.empty:
        st.warning("Nenhum ponto após filtros.")
    else:
        c1, c2 = st.columns(2)
        with c1:
            st.altair_chart(chart_cl_vs_L(dff), use_container_width=True)
        with c2:
            st.altair_chart(chart_tempo_vs_L(dff), use_container_width=True)

        st.divider()
        st.subheader("Exportar")
        # CSV filtrado
        csv_bytes = dff.to_csv(index=False).encode("utf-8")
        st.download_button("Baixar CSV filtrado", data=csv_bytes, file_name="dataset_filtrado.csv", mime="text/csv")

        # PNG (requer vl-convert-python)
        try:
            import vl_convert as vlc
            cl_png = vlc.vegalite_to_png(chart_cl_vs_L(dff).to_dict())
            tmp_name = f"cl_vs_L_{int(time.time())}.png"
            st.download_button("Baixar gráfico CL vs L (PNG)", data=cl_png, file_name=tmp_name, mime="image/png")
        except Exception:
            st.info("Para baixar PNGs, instale `vl-convert-python`.")
else:
    st.info("Base vazia. Faça upload de arquivos .txt acima.")

st.divider()
st.caption("Persistência local via SQLite. Consulte o README para deploy em nuvem.")
