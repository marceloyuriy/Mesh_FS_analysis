import altair as alt
import pandas as pd

def chart_cl_vs_L(df: pd.DataFrame) -> alt.Chart:
    return (
        alt.Chart(df)
        .mark_line(point=True)
        .encode(
            x=alt.X('L_m', title='Tamanho do Plano (L_m)'),
            y=alt.Y('CL_Asa_Stab', title='CL', scale=alt.Scale(zero=False)),
            color=alt.Color('Malha', title='Malha'),
            tooltip=['Malha', 'L_m', 'h', 'Tempo_Execucao',
                     alt.Tooltip('Tempo_Execucao_min', title='Tempo (min)'),
                     alt.Tooltip('Tempo_Execucao_h', title='Tempo (h)'),
                     'CL_Asa_Stab']
        )
        .properties(title='CL vs. Tamanho do Plano (por Malha)')
        .interactive()
    )

def chart_tempo_vs_L(df: pd.DataFrame) -> alt.Chart:
    return (
        alt.Chart(df)
        .mark_line(point=True)
        .encode(
            x=alt.X('L_m', title='Tamanho do Plano (L_m)'),
            y=alt.Y('Tempo_Execucao_min', title='Tempo de Execução (min)'),
            color=alt.Color('Malha', title='Malha'),
            tooltip=['Malha', 'L_m', 'Tempo_Execucao',
                     alt.Tooltip('Tempo_Execucao_min', title='Tempo (min)'),
                     alt.Tooltip('Tempo_Execucao_h', title='Tempo (h)')]
        )
        .properties(title='Tempo de Execução vs. Tamanho do Plano (por Malha)')
        .interactive()
    )
