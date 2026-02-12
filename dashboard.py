import streamlit as st
import pandas as pd
import plotly.graph_objects as go

# 1. Configuración de la página
st.set_page_config(page_title="Dashboard Usabilidad Holos", layout="wide")

LINK_1 = "https://docs.google.com/spreadsheets/d/e/2PACX-1vSWiXR7BLxwzX2wtD_uF59pvxtus8BL5iqgymKSh2-Llwt6smOJzR7ROUxICr57DA/pub?gid=1638907402&single=true&output=csv"
LINK_2 = "https://docs.google.com/spreadsheets/d/e/2PACX-1vSWiXR7BLxwzX2wtD_uF59pvxtus8BL5iqgymKSh2-Llwt6smOJzR7ROUxICr57DA/pub?gid=1341962834&single=true&output=csv"

@st.cache_data(ttl=5)
def cargar_datos_seguro():
    try:
        df = pd.concat([pd.read_csv(LINK_1), pd.read_csv(LINK_2)], ignore_index=True)
        df.columns = [str(c).strip() for c in df.columns]
        
        # Procesamiento limpio de columnas
        datos = pd.DataFrame()
        datos['Empresa'] = df.iloc[:, 0].astype(str).str.strip()
        datos['Semana_Txt'] = df.iloc[:, 1].astype(str).str.strip()
        
        # Limpieza de usabilidad
        def to_perc(x):
            try:
                v = float(str(x).replace('%','').replace(',','.'))
                return v/100 if v > 1.1 else v
            except: return 0.0
        
        datos['Valor'] = df.iloc[:, 7].apply(to_perc)
        datos['Mes_N'] = pd.to_numeric(df.iloc[:, 9], errors='coerce').fillna(0).astype(int)
        datos['Anio_N'] = pd.to_numeric(df.iloc[:, 11], errors='coerce').fillna(0).astype(int)
        
        return datos[datos['Anio_N'] >= 2025]
    except Exception as e:
        st.error(f"Error de conexión: {e}")
        return pd.DataFrame()

df_raw = cargar_datos_seguro()

if not df_raw.empty:
    # --- SIDEBAR ---
    with st.sidebar:
        st.header("⚙️ Configuración")
        interfaz = st.radio("Seleccionar Vista:", ["Resumen Ejecutivo (Mensual)", "Reporte Operativo (Semanal)"])
        
        empresa_list = sorted(df_raw['Empresa'].unique())
        empresa_sel = st.selectbox("Empresa:", ["Todas las Empresas"] + empresa_list)
        
        anios_sel = st.multiselect("Años:", [2026, 2025], default=[2026, 2025])
        
        m_nombres = {1:'Ene', 2:'Feb', 3:'Mar', 4:'Abr', 5:'May', 6:'Jun', 7:'Jul', 8:'Ago', 9:'Sep', 10:'Oct', 11:'Nov', 12:'Dic'}
        meses_sel = st.multiselect("Meses:", list(m_nombres.keys()), default=[1, 2], format_func=lambda x: m_nombres.get(x))

    # Filtro base
    df_f = df_raw[(df_raw['Anio_N'].isin(anios_sel)) & (df_raw['Mes_N'].isin(meses_sel))].copy()
    if empresa_sel != "Todas las Empresas":
        df_f = df_f[df_f['Empresa'] == empresa_sel]

    # --- LÓGICA DE INTERFACES ---
    if "Ejecutivo" in interfaz:
        st.title("📊 Resumen Ejecutivo (Totales Mensuales)")
        # Solo tomamos las filas que dicen "total"
        df_plot = df_f[df_f['Semana_Txt'].str.lower().contains('total', na=False)].copy()
        df_plot = df_plot.groupby(['Anio_N', 'Mes_N']).agg({'Valor':'mean'}).reset_index()
        df_plot = df_plot.sort_values(['Anio_N', 'Mes_N'])
        df_plot['Eje_X'] = df_plot['Mes_N'].map(m_nombres)
    else:
        st.title("📉 Reporte Operativo (Progreso por Semanas)")
        # Excluimos los totales
        df_plot = df_f[~df_f['Semana_Txt'].str.lower().contains('total', na=False)].copy()
        
        # Ordenar semanas: 1era, 2da, 3era, 4ta
        rank_sem = {'1era semana':1, '2da semana':2, '3era semana':3, '4ta semana':4}
        df_plot['sem_rank'] = df_plot['Semana_Txt'].str.lower().map(rank_sem).fillna(5)
        
        df_plot = df_plot.groupby(['Anio_N', 'Mes_N', 'Semana_Txt', 'sem_rank']).agg({'Valor':'mean'}).reset_index()
        df_plot = df_plot.sort_values(['Anio_N', 'Mes_N', 'sem_rank'])
        df_plot['Eje_X'] = df_plot.apply(lambda x: f"{m_nombres.get(x['Mes_N'])}-{x['Semana_Txt']}", axis=1)

    # --- GRÁFICO ---
    if not df_plot.empty:
        fig = go.Figure()
        colores = {2025: "#FF9F86", 2026: "#A9C1F5"}

        for anio in sorted(anios_sel):
            df_anio = df_plot[df_plot['Anio_N'] == anio]
            if not df_anio.empty:
                fig.add_trace(go.Scatter(
                    x=df_anio['Eje_X'], 
                    y=df_anio['Valor'],
                    name=f"Año {anio}",
                    mode='lines+markers+text',
                    text=[f"{v:.1%}" for v in df_anio['Valor']],
                    textposition="top center",
                    line=dict(color=colores.get(anio, "#333"), width=4),
                    connectgaps=True
                ))

        fig.update_layout(
            yaxis=dict(tickformat=".0%", range=[0, 1.1], gridcolor="#f0f0f0"),
            xaxis=dict(gridcolor="#f0f0f0"),
            plot_bgcolor="white",
            height=500,
            margin=dict(l=20, r=20, t=40, b=20)
        )
        st.plotly_chart(fig, use_container_width=True)
    else:
        st.warning("No hay datos que coincidan con los filtros seleccionados.")

else:
    st.info("Conectando con el servidor de datos...")
