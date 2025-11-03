import os, time
import streamlit as st
import pandas as pd
from parser_cfd import parse_uploaded_txt
from storage import upsert_rows, fetch_dataframe, export_csv, DEFAULT_DB_PATH
from charts import chart_cl_vs_L, chart_tempo_vs_L

st.set_page_config(page_title="CFD Post-Processing", page_icon="🌀", layout="wide")

st.title("🌀 Pós-processamento CFD – Upload incremental com persistência")
st.caption("Envie arquivos .txt de resultados; a base é atualizada de forma idempotente e os gráficos são re-renderizados.")

with st.sidebar:
    st.header("Configuração")
    db_path = st.text_input("Caminho do banco (SQLite)", value=DEFAULT_DB_PATH)
    st.write(f"DB em: `{db_path}`")
    st.divider()
    st.markdown("**Ajuda**")
    st.write("• Persistência em SQLite com hash para evitar duplicatas.")
    st.write("• Nome do arquivo no padrão do pipeline; conteúdo com linhas Asa_right/Stab_direita.")

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
            try:
                os.makedirs("uploads", exist_ok=True)
                with open(os.path.join("uploads", up.name), "wb") as f:
                    f.write(data)
            except Exception:
                pass

    if not rows:
        st.warning("Nenhum arquivo válido reconhecido.")
    else:
        ins, dup = upsert_rows(rows, db_path=db_path)
        st.success(f"Inseridos: {ins} | Ignorados (duplicados): {dup}")
        with st.expander("Prévia das linhas parseadas"):
            st.dataframe(pd.DataFrame(rows))

st.subheader("Base de dados")
df = fetch_dataframe(db_path=db_path)
st.write(f"Total de pontos: **{len(df)}**")
st.dataframe(df, use_container_width=True)

st.subheader("Gráficos")
if len(df) > 0:
    col1, col2 = st.columns(2)
    with col1:
        malhas = sorted(df["Malha"].unique().tolist())
        sel_malha = st.multiselect("Filtrar por Malha", options=malhas, default=malhas)
    with col2:
        Lmin, Lmax = float(df["L_m"].min()), float(df["L_m"].max())
        sel_L = st.slider("Filtrar por L_m", min_value=Lmin, max_value=Lmax, value=(Lmin, Lmax), step=0.001)

    dff = df[(df["Malha"].isin(sel_malha)) & (df["L_m"] >= sel_L[0]) & (df["L_m"] <= sel_L[1])].copy()

    c1, c2 = st.columns(2)
    with c1:
        st.altair_chart(chart_cl_vs_L(dff), use_container_width=True)
    with c2:
        st.altair_chart(chart_tempo_vs_L(dff), use_container_width=True)

    st.divider()
    st.subheader("Exportar")
    csv_bytes = dff.to_csv(index=False).encode("utf-8")
    st.download_button("Baixar CSV filtrado", data=csv_bytes, file_name="dataset_filtrado.csv", mime="text/csv")

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
