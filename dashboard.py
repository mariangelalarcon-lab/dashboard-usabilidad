import streamlit as st
import pandas as pd
import plotly.graph_objects as go

# 1. Configuración de pantalla
st.set_page_config(page_title="Holos | BI", layout="wide")

# Enlaces de datos
LINK_1 = "https://docs.google.com/spreadsheets/d/e/2PACX-1vSWiXR7BLxwzX2wtD_uF59pvxtus8BL5iqgymKSh2-Llwt6smOJzR7ROUxICr57DA/pub?gid=1638907402&single=true&output=csv"
LINK_2 = "https://docs.google.com/spreadsheets/d/e/2PACX-1vSWiXR7BLxwzX2wtD_uF59pvxtus8BL5iqgymKSh2-Llwt6smOJzR7ROUxICr57DA/pub?gid=1341962834&single=true&output=csv"

# Paleta Holos
SKY, LEAF, SEA, CORAL, BLACK, WHITE = "#D1E9F6", "#F1FB8C", "#A9C1F5", "#FF9F86", "#000000", "#FFFFFF"

@st.cache_data(ttl=60)
def cargar_data():
    try:
        df1 = pd.read_csv(LINK_1)
        df2 = pd.read_csv(LINK_2)
        df = pd.concat([df1, df2], ignore_index=True)
        df.columns = [str(c).strip() for c in df.columns]
        
        # Identificación de columnas
        c_usa = next((c for c in df.columns if 'Usabilidad' in c or 'Engagement' in c), None)
        c_emp = next((c for c in df.columns if 'Empresa' in c), df.columns[0])
        c_mes = next((c for c in df.columns if 'Mes' in c), None)
        c_ani = next((c for c in df.columns if 'Año' in c or 'Anio' in c), None)
        # Columnas para cálculo real
        c_colab = next((c for c in df.columns if 'Colaboradores' in c), None)
        c_util = next((c for c in df.columns if 'utilizaron' in c), None)

        def limpiar_num(val):
            try:
                s = str(val).replace('%', '').replace(',', '.').strip()
                n = float(s)
                return n / 100.0 if n > 1.1 else n
            except: return 0.0

        df['Usabilidad_V'] = df[c_usa].apply(limpiar_num)
        df['Colab_V'] = pd.to_numeric(df[c_colab], errors='coerce').fillna(0)
        df['Util_V'] = pd.to_numeric(df[c_util], errors='coerce').fillna(0)
        df['Anio_V'] = pd.to_numeric(df[c_ani], errors='coerce').fillna(0).astype(int)
        df['Mes_V'] = pd.to_numeric(df[c_mes], errors='coerce').fillna(0).astype(int)
        df['Empresa_V'] = df[c_emp].astype(str).str.strip()
        
        return df, 'Empresa_V', 'Anio_V', 'Mes_V'
    except Exception as e:
        return pd.DataFrame(), str(e), None, None

df, col_emp, col_ani, col_mes = cargar_data()

if not df.empty:
    with st.sidebar:
        st.header("Filtros")
        lista_empresas = sorted([e for e in df[col_emp].unique() if str(e) not in ['nan', 'None']])
        empresa_sel = st.selectbox("Empresa Target", ["Todas las Empresas"] + lista_empresas)
        anios_disp = sorted([a for a in df[col_ani].unique() if a > 2020], reverse=True)
        anios_sel = st.multiselect("Años", anios_disp, default=anios_disp)
        meses_map = {1:'Ene', 2:'Feb', 3:'Mar', 4:'Abr', 5:'May', 6:'Jun', 7:'Jul', 8:'Ago', 9:'Set', 10:'Oct', 11:'Nov', 12:'Dic'}
        meses_sel = st.multiselect("Meses", sorted(meses_map.keys()), default=sorted(meses_map.keys()), format_func=lambda x: meses_map[x])

    st.title(f"Reporte: {empresa_sel}")

    # --- LÓGICA DE CÁLCULO DINÁMICA ---
    def obtener_metrica_final(df_contexto, es_todas):
        if df_contexto.empty: return 0.0
        if es_todas:
            # Lógica Excel: Promedio de los porcentajes de cada fila
            return df_contexto['Usabilidad_V'].mean()
        else:
            # Lógica Real x Empresa: Suma Usuarios / Suma Colaboradores
            total_colab = df_contexto['Colab_V'].sum()
            total_util = df_contexto['Util_V'].sum()
            return total_util / total_colab if total_colab > 0 else df_contexto['Usabilidad_V'].mean()

    # Filtrado
    df_f = df[(df[col_ani].isin(anios_sel)) & (df[col_mes].isin(meses_sel))].copy()
    es_global = (empresa_sel == "Todas las Empresas")
    if not es_global:
        df_f = df_f[df_f[col_emp] == empresa_sel]

    # Gauges
    colores_config = {2023: WHITE, 2024: LEAF, 2025: CORAL, 2026: SEA}
    anios_activos = sorted(df_f[col_ani].unique())
    if anios_activos:
        cols = st.columns(len(anios_activos))
        for i, anio in enumerate(anios_activos):
            with cols[i]:
                df_anio = df_f[df_f[col_ani] == anio]
                val = obtener_metrica_final(df_anio, es_global)
                fig = go.Figure(go.Indicator(
                    mode="gauge+number", value=val*100,
                    number={'suffix': "%", 'valueformat': '.1f'},
                    title={'text': f"Promedio {anio}"},
                    gauge={'axis': {'range': [0, 100]}, 'bar': {'color': BLACK},
                           'steps': [{'range': [0, 100], 'color': colores_config.get(anio, WHITE)}]}
                ))
                fig.update_layout(height=250, margin=dict(l=20, r=20, t=40, b=20))
                st.plotly_chart(fig, use_container_width=True)

    # Gráfico de Evolución
    st.subheader("Curva de Engagement")
    if not df_f.empty:
        # Agrupamos para la línea según la lógica seleccionada
        if es_global:
            df_linea = df_f.groupby([col_ani, col_mes])['Usabilidad_V'].mean().reset_index()
        else:
            df_linea = df_f.groupby([col_ani, col_mes]).apply(
                lambda x: (x['Util_V'].sum() / x['Colab_V'].sum()) if x['Colab_V'].sum() > 0 else x['Usabilidad_V'].mean()
            ).reset_index(name='Usabilidad_V')
        
        df_linea = df_linea.sort_values([col_ani, col_mes])
        fig_l = go.Figure()
        for anio in sorted(anios_sel):
            df_a = df_linea[df_linea[col_ani] == anio]
            if not df_a.empty:
                fig_l.add_trace(go.Scatter(
                    x=[meses_map.get(m) for m in df_a[col_mes]], y=df_a['Usabilidad_V'],
                    name=str(anio), mode='lines+markers+text',
                    text=[f"{v:.1%}" for v in df_a['Usabilidad_V']], textposition="top center",
                    line=dict(color=colores_config.get(anio, BLACK), width=3)
                ))
        fig_l.update_layout(yaxis=dict(tickformat=".0%", range=[0, 1.1]), height=400)
        st.plotly_chart(fig_l, use_container_width=True)

    with st.expander("Registros"):
        st.dataframe(df_f)
