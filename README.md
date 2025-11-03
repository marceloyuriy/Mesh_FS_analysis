# CFD Post-Processing (Streamlit)

App Streamlit para pós-processar logs .txt de CFD:
- Upload incremental de arquivos
- Parse do nome do arquivo e do conteúdo (CL da asa + estabilizador)
- Persistência em SQLite (idempotente por hash)
- Gráficos Altair interativos (CL vs L_m e Tempo vs L_m)
- Exportação de CSV e (opcional) PNG

## Rodando localmente

```bash
python -m venv .venv && source .venv/bin/activate  # (Windows: .venv\Scripts\activate)
pip install -r requirements.txt
streamlit run streamlit_app.py
```

A base persiste em `data/cfd.db`. Os uploads ficam em `uploads/`.

## Padrão esperado dos arquivos

O nome deve seguir algo como:
`result03_plano_solo_L110.0000m_malha_250x250_h2.0580_55_27min.txt`

O conteúdo deve conter linhas iniciadas por `Asa_right` e `Stab_direita`, com o CL na 5ª coluna (índice 4).
