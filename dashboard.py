import streamlit as st
import pandas as pd
import plotly.graph_objects as go

# 1. Configuración de Pantalla
st.set_page_config(page_title="Holos | Business Intelligence", layout="wide")

LINK_1 = "https://docs.google.com/spreadsheets/d/e/2PACX-1vSWiXR7BLxwzX2wtD_uF59pvxtus8BL5iqgymKSh2-Llwt6smOJzR7ROUxICr57DA/pub?gid=1638907402&single=true&output=csv"
LINK_2 = "https://docs.google.com/spreadsheets/d/e/2PACX-1vSWiXR7BLxwzX2wtD_uF59pvxtus8BL5iqgymKSh2-Llwt6smOJzR7ROUxICr57DA/pub?gid=1341962834&single=true&output=csv"

SKY, LEAF, SEA, CORAL, BLACK = "#D1E9F6", "#F1FB8C", "#A9C1F5", "#FF9F86", "#000000"

@st.cache_data(ttl=5)
def cargar_data():
    try:
        df = pd.concat([pd.read_csv(LINK_1), pd.read_csv(LINK_2)], ignore_index=True)
        df.columns = [str(c).strip() for c in df.columns]
        
        # Limpieza de datos por posición para evitar errores de nombres
        df['Empresa_V'] = df.iloc[:, 0].astype(str).str.strip()
        # NORMALIZACIÓN TOTAL: Quitamos espacios y pasamos a minúsculas
        df['Semana_V'] = df.iloc[:, 1].astype(str).str.strip().str.lower()
        df['Mes_V'] = pd.to_numeric(df.iloc[:, 9], errors='coerce').fillna(0).astype(int)
        df['Anio_V'] = pd.to_numeric(df.iloc[:, 11], errors='coerce').fillna(0).astype(int)
        
        def limpiar_pct(val):
            try:
                s = str(val).replace('%', '').replace(',', '.').strip()
                n = float(s)
                return n / 100.0 if n > 1.1 else n
            except: return 0.0
        
        df['Usabilidad_V'] = df.iloc[:, 7].apply(limpiar_pct)
        # Filtramos solo data real (evitamos filas vacías del Excel)
        df = df[(df['Anio_V'] >= 2025) & (df['Empresa_V'] != 'nan') & (df['Usabilidad_V'] > 0)]
        return df
    except Exception as e:
        st.error(f"Error de conexión: {e}")
        return pd.DataFrame()

df = cargar_data()

if not df.empty:
    with st.sidebar:
        st.header("🎛️ Filtros Pro")
        modo = st.radio("Ver datos como:", ["Resumen Mensual (Cierres)", "Detalle Semanal (Avance)"])
        empresa_sel = st.selectbox("Seleccionar Empresa", ["Todas las Empresas"] + sorted(df['Empresa_V'].unique()))
        anios_sel = st.multiselect("Años", [2026, 2025], default=[2026, 2025])
        meses_sel = st.multiselect("Meses", [1, 2], default=[1, 2], 
                                   format_func=lambda x: {1:'Ene', 2:'Feb'}.get(x))

    # Filtrado lógico
    mask = (df['Anio_V'].isin(anios_sel)) & (df['Mes_V'].isin(meses_sel))
    if empresa_sel != "Todas las Empresas":
        mask &= (df['Empresa_V'] == empresa_sel)
    df_f = df[mask].copy()

    # Separación por tipo de reporte
    if "Resumen" in modo:
        df_vis = df_f[df_f['Semana_V'].str.contains('total', na=False)]
    else:
        df_vis = df_f[~df_f['Semana_V'].str.contains('total', na=False)]

    st.title(f"📊 Dashboard: {empresa_sel}")

    if not df_vis.empty:
        # MAPEO DE SEMANAS (Para que el orden sea perfecto y Febrero aparezca después de Enero)
        sem_map = {'1era semana': 1, '2da semana': 2, '3era semana': 3, '4ta semana': 4}
        df_vis['sem_idx'] = df_vis['Semana_V'].map(sem_map).fillna(0)
        # Ordenamos cronológicamente: Año -> Mes -> Semana
        df_vis = df_vis.sort_values(['Anio_V', 'Mes_V', 'sem_idx'])

        fig = go.Figure()
        colores = {2025: CORAL, 2026: SEA}
        mes_names = {1:'Ene', 2:'Feb'}

        for a in sorted(anios_sel, reverse=True):
            d_plot = df_vis[df_vis['Anio_V'] == a]
            # AGRUPACIÓN: Promediamos por semana para evitar el error de bajada de la semana 4
            d_grp = d_plot.groupby(['Mes_V', 'Semana_V', 'sem_idx'])['Usabilidad_V'].mean().reset_index()
            d_grp = d_grp.sort_values(['Mes_V', 'sem_idx'])
            
            x_labels = [f"{mes_names.get(m)}-{s.capitalize()}" for m, s in zip(d_grp['Mes_V'], d_grp['Semana_V'])]
            
            fig.add_trace(go.Scatter(
                x=x_labels, y=d_grp['Usabilidad_V'],
                name=f"Año {a}", mode='lines+markers+text',
                line=dict(color=colores.get(a, BLACK), width=4 if a == 2026 else 2),
                text=[f"{v:.1%}" for v in d_grp['Usabilidad_V']],
                textposition="top center",
                connectgaps=True # Esto permite que la línea siga si faltan semanas
            ))

        fig.update_layout(yaxis=dict(tickformat=".0%", range=[0, 1.1]), hovermode="x unified", height=500)
        st.plotly_chart(fig, use_container_width=True)

        # --- ANÁLISIS CON IA (INTEGRADO) ---
        st.markdown("### 🧠 Informe de Desempeño Holos")
        try:
            val_ene = df_vis[(df_vis['Anio_V']==2026) & (df_vis['Mes_V']==1)]['Usabilidad_V'].iloc[-1]
            val_feb = df_vis[(df_vis['Anio_V']==2026) & (df_vis['Mes_V']==2)]['Usabilidad_V'].iloc[-1] if 2 in meses_sel else 0
            
            status = "subiendo 📈" if val_feb > val_ene else "en observación 📉"
            st.success(f"**Análisis:** La semana 1 de Febrero muestra un **{val_feb:.1%}**. Comparado con el cierre de Enero ({val_ene:.1%}), el engagement está {status}.")
        except:
            st.info("Llenando datos de Febrero... La comparativa aparecerá al completar la primera semana.")

    else:
        st.warning("No hay datos. Asegúrate de que en el Excel las columnas J y L tengan los números 1, 2 y 2026.")

    with st.expander("🔍 Auditoría de Datos (Verifica aquí si Febrero aparece)"):
        st.dataframe(df_vis[['Empresa_V', 'Anio_V', 'Mes_V', 'Semana_V', 'Usabilidad_V']].sort_values(['Anio_V', 'Mes_V', 'sem_idx']))
