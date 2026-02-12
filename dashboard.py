import streamlit as st
import pandas as pd
import plotly.graph_objects as go

# Configuración de página Pro
st.set_page_config(page_title="Holos BI | Reporte Dual", layout="wide")

LINK_1 = "https://docs.google.com/spreadsheets/d/e/2PACX-1vSWiXR7BLxwzX2wtD_uF59pvxtus8BL5iqgymKSh2-Llwt6smOJzR7ROUxICr57DA/pub?gid=1638907402&single=true&output=csv"
LINK_2 = "https://docs.google.com/spreadsheets/d/e/2PACX-1vSWiXR7BLxwzX2wtD_uF59pvxtus8BL5iqgymKSh2-Llwt6smOJzR7ROUxICr57DA/pub?gid=1341962834&single=true&output=csv"

@st.cache_data(ttl=5)
def cargar_base():
    try:
        # Carga de datos crudos
        df1 = pd.read_csv(LINK_1)
        df2 = pd.read_csv(LINK_2)
        df = pd.concat([df1, df2], ignore_index=True)
        df.columns = [str(c).strip() for c in df.columns]
        
        # Creación de DataFrame limpio desde cero para evitar errores de duplicados
        limpio = pd.DataFrame()
        limpio['empresa'] = df.iloc[:, 0].astype(str).str.strip()
        limpio['semana_orig'] = df.iloc[:, 1].astype(str).str.strip()
        limpio['semana_low'] = limpio['semana_orig'].str.lower()
        
        # Limpieza de valores numéricos
        def clean_val(x):
            try:
                v = float(str(x).replace('%', '').replace(',', '.'))
                return v/100 if v > 1.1 else v
            except: return 0.0
            
        limpio['valor'] = df.iloc[:, 7].apply(clean_val)
        limpio['mes'] = pd.to_numeric(df.iloc[:, 9], errors='coerce').fillna(0).astype(int)
        limpio['anio'] = pd.to_numeric(df.iloc[:, 11], errors='coerce').fillna(0).astype(int)
        
        return limpio[limpio['anio'] >= 2025]
    except Exception as e:
        st.error(f"Error técnico al leer el Excel: {e}")
        return pd.DataFrame()

df_raw = cargar_base()

if not df_raw.empty:
    # --- BARRA LATERAL (SIDEBAR) ---
    with st.sidebar:
        st.header("🏢 Menú Principal")
        interfaz = st.radio("Seleccionar Vista:", ["Dashboard Ejecutivo", "Reporte Operativo"])
        
        st.markdown("---")
        # Filtros dinámicos
        empresa_sel = st.selectbox("Empresa:", ["Todas"] + sorted(df_raw['empresa'].unique().tolist()))
        anios_sel = st.multiselect("Años:", sorted(df_raw['anio'].unique(), reverse=True), default=[2026, 2025])
        
        meses_dict = {1:'Ene', 2:'Feb', 3:'Mar', 4:'Abr', 5:'May', 6:'Jun', 7:'Jul', 8:'Ago', 9:'Set', 10:'Oct', 11:'Nov', 12:'Dic'}
        meses_sel = st.multiselect("Meses:", list(meses_dict.keys()), default=[1, 2], format_func=lambda x: meses_dict.get(x))

    # --- FILTRADO DE DATOS ---
    df_f = df_raw[(df_raw['anio'].isin(anios_sel)) & (df_raw['mes'].isin(meses_sel))].copy()
    if empresa_sel != "Todas":
        df_f = df_f[df_f['empresa'] == empresa_sel]

    # --- MODO EJECUTIVO (Solo Totales) ---
    if interfaz == "Dashboard Ejecutivo":
        st.title("📊 Resumen Ejecutivo (Cierres Mensuales)")
        # Filtramos solo lo que diga "total"
        df_vis = df_f[df_f['semana_low'].str.contains('total', na=False)].copy()
        group_cols = ['anio', 'mes']
        sort_cols = ['anio', 'mes']
        df_vis['eje_x'] = df_vis['mes'].map(meses_dict)

    # --- MODO OPERATIVO (Semanas 1 a 4) ---
    else:
        st.title("📈 Reporte Operativo (Avance Semanal)")
        # Excluimos los totales
        df_vis = df_f[~df_f['semana_low'].str.contains('total', na=False)].copy()
        
        # Mapeo de orden para que la semana 4 nunca baje por error de orden
        rank_map = {'1era semana': 1, '2da semana': 2, '3era semana': 3, '4ta semana': 4}
        df_vis['rank'] = df_vis['semana_low'].map(rank_map).fillna(5)
        
        group_cols = ['anio', 'mes', 'semana_orig', 'rank']
        sort_cols = ['anio', 'mes', 'rank']
        df_vis['eje_x'] = df_vis.apply(lambda x: f"{meses_dict.get(x['mes'])}-{x['semana_orig']}", axis=1)

    # --- GENERACIÓN DE GRÁFICA ---
    if not df_vis.empty:
        # Agrupación para evitar duplicados y errores de "Already Exists"
        df_plot = df_vis.groupby(group_cols).agg({'valor': 'mean'}).reset_index()
        df_plot = df_plot.sort_values(sort_cols)
        
        # Re-crear etiquetas del eje X después del groupby para asegurar orden
        if interfaz == "Dashboard Ejecutivo":
            df_plot['label'] = df_plot['mes'].map(meses_dict)
        else:
            df_plot['label'] = df_plot.apply(lambda x: f"{meses_dict.get(x['mes'])}-{x['semana_orig']}", axis=1)

        fig = go.Figure()
        colores = {2025: "#FF9F86", 2026: "#A9C1F5"} # Coral y Celeste Holos

        for a in sorted(anios_sel):
            d_anio = df_plot[df_plot['anio'] == a]
            if not d_anio.empty:
                fig.add_trace(go.Scatter(
                    x=d_anio['label'], 
                    y=d_anio['valor'],
                    name=f"Año {a}",
                    mode='lines+markers+text',
                    text=[f"{v:.1%}" for v in d_anio['valor']],
                    textposition="top center",
                    line=dict(width=4, color=colores.get(a, "#333")),
                    connectgaps=True
                ))

        fig.update_layout(
            yaxis=dict(tickformat=".0%", range=[0, 1.1], gridcolor="#f0f0f0"),
            xaxis=dict(title="Periodo", gridcolor="#f0f0f0"),
            plot_bgcolor="white",
            height=500,
            hovermode="x unified"
        )
        st.plotly_chart(fig, use_container_width=True)
    else:
        st.warning("No hay datos que coincidan con los filtros. Revisa que en el Excel las celdas digan '1era semana' o 'Mes total'.")

    # Tabla de auditoría para que tú mismo veas qué está leyendo el código
    with st.expander("🔍 Ver tabla de datos procesados"):
        st.dataframe(df_vis[['empresa', 'anio', 'mes', 'semana_orig', 'valor']])
else:
    st.error("No se detectan datos. Verifica que el Google Sheet esté Publicado como Web (CSV).")
