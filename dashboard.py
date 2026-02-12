import streamlit as st
import pandas as pd
import plotly.graph_objects as go

# 1. Configuración Pro
st.set_page_config(page_title="Holos | BI Dashboard", layout="wide")

LINK_1 = "https://docs.google.com/spreadsheets/d/e/2PACX-1vSWiXR7BLxwzX2wtD_uF59pvxtus8BL5iqgymKSh2-Llwt6smOJzR7ROUxICr57DA/pub?gid=1638907402&single=true&output=csv"
LINK_2 = "https://docs.google.com/spreadsheets/d/e/2PACX-1vSWiXR7BLxwzX2wtD_uF59pvxtus8BL5iqgymKSh2-Llwt6smOJzR7ROUxICr57DA/pub?gid=1341962834&single=true&output=csv"

@st.cache_data(ttl=5)
def cargar_limpiar_data():
    try:
        df = pd.concat([pd.read_csv(LINK_1), pd.read_csv(LINK_2)], ignore_index=True)
        df.columns = [str(c).strip() for c in df.columns]
        
        # Procesamiento ultra-seguro
        res = pd.DataFrame()
        res['Empresa'] = df.iloc[:, 0].astype(str).str.strip()
        # Convertimos a string y minúsculas para que 'Total' y 'total' sean lo mismo
        res['Semana_Raw'] = df.iloc[:, 1].astype(str).str.strip()
        res['Semana_Lower'] = res['Semana_Raw'].str.lower()
        
        def to_pct(x):
            try:
                v = float(str(x).replace('%','').replace(',','.'))
                return v/100 if v > 1.1 else v
            except: return 0.0
            
        res['Valor'] = df.iloc[:, 7].apply(to_pct)
        res['Mes_N'] = pd.to_numeric(df.iloc[:, 9], errors='coerce').fillna(0).astype(int)
        res['Anio_N'] = pd.to_numeric(df.iloc[:, 11], errors='coerce').fillna(0).astype(int)
        
        return res[res['Anio_N'] >= 2025]
    except Exception as e:
        st.error(f"Error cargando datos: {e}")
        return pd.DataFrame()

df_raw = cargar_limpiar_data()

if not df_raw.empty:
    with st.sidebar:
        st.header("⚡ Navegación")
        interfaz = st.radio("Tipo de Análisis:", ["Ejecutivo (Cierres Mensuales)", "Operativo (Avance Semanal)"])
        
        empresa_sel = st.selectbox("Filtrar Empresa:", ["Todas las Empresas"] + sorted(df_raw['Empresa'].unique()))
        anios_sel = st.multiselect("Años:", [2026, 2025], default=[2026, 2025])
        
        m_map = {1:'Ene', 2:'Feb', 3:'Mar', 4:'Abr', 5:'May', 6:'Jun', 7:'Jul', 8:'Ago', 9:'Sep', 10:'Oct', 11:'Nov', 12:'Dic'}
        meses_sel = st.multiselect("Meses:", list(m_map.keys()), default=[1, 2], format_func=lambda x: m_map.get(x))

    # Filtro base por sidebar
    mask = (df_raw['Anio_N'].isin(anios_sel)) & (df_raw['Mes_N'].isin(meses_sel))
    if empresa_sel != "Todas las Empresas":
        mask &= (df_raw['Empresa'] == empresa_sel)
    
    df_base = df_raw[mask].copy()

    # --- LÓGICA DE INTERFACES SIN ERRORES ---
    if "Ejecutivo" in interfaz:
        st.title("📊 Resumen Ejecutivo: Cierres Totales")
        # Filtramos filas que contienen 'total'
        df_plot = df_base[df_base['Semana_Lower'].str.contains('total', na=False)].copy()
        label_x = 'Mes_N'
        sort_order = ['Anio_N', 'Mes_N']
    else:
        st.title("📉 Reporte Operativo: Progreso Semanal")
        # Excluimos filas que contienen 'total'
        df_plot = df_base[~df_base['Semana_Lower'].str.contains('total', na=False)].copy()
        
        # Mapeo de orden para evitar bajones de semana 4
        rank_map = {'1era semana':1, '2da semana':2, '3era semana':3, '4ta semana':4}
        df_plot['rank'] = df_plot['Semana_Lower'].map(rank_map).fillna(5)
        label_x = 'Semana_Raw'
        sort_order = ['Anio_N', 'Mes_N', 'rank']

    # --- RENDERIZADO DE GRÁFICA ---
    if not df_plot.empty:
        # Agrupamos promediando por si hay múltiples empresas
        df_fin = df_plot.groupby(['Anio_N', 'Mes_N', label_x] + (['rank'] if "Operativo" in interfaz else [])).agg({'Valor':'mean'}).reset_index()
        df_fin = df_fin.sort_values(sort_order)
        
        # Etiqueta unificada para el eje X
        df_fin['Etiqueta'] = df_fin.apply(lambda x: f"{m_map.get(x['Mes_N'])}-{x[label_x]}", axis=1)

        fig = go.Figure()
        colores = {2025: "#FF9F86", 2026: "#A9C1F5"}

        for anio in sorted(anios_sel):
            d_anio = df_fin[df_fin['Anio_N'] == anio]
            if not d_anio.empty:
                fig.add_trace(go.Scatter(
                    x=d_anio['Etiqueta'], y=d_anio['Valor'],
                    name=f"Año {anio}", mode='lines+markers+text',
                    text=[f"{v:.1%}" for v in d_anio['Valor']],
                    textposition="top center",
                    line=dict(color=colores.get(anio, "#333"), width=4),
                    connectgaps=True
                ))

        fig.update_layout(yaxis=dict(tickformat=".0%", range=[0, 1.1]), hovermode="x unified", height=500)
        st.plotly_chart(fig, use_container_width=True)
    else:
        st.info("No hay información suficiente para estos filtros. Verifica que las semanas estén marcadas como '1era semana' o 'Mes total'.")

else:
    st.error("Esperando datos del Google Sheet...")
