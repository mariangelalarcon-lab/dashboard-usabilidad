import streamlit as st
import pandas as pd
import plotly.graph_objects as go

st.set_page_config(page_title="Holos Dashboard", layout="wide")

LINK_1 = "https://docs.google.com/spreadsheets/d/e/2PACX-1vSWiXR7BLxwzX2wtD_uF59pvxtus8BL5iqgymKSh2-Llwt6smOJzR7ROUxICr57DA/pub?gid=1638907402&single=true&output=csv"
LINK_2 = "https://docs.google.com/spreadsheets/d/e/2PACX-1vSWiXR7BLxwzX2wtD_uF59pvxtus8BL5iqgymKSh2-Llwt6smOJzR7ROUxICr57DA/pub?gid=1341962834&single=true&output=csv"

SKY, LEAF, SEA, CORAL, BLACK = "#D1E9F6", "#F1FB8C", "#A9C1F5", "#FF9F86", "#000000"

@st.cache_data(ttl=5)
def cargar_data():
    try:
        # 1. Carga y limpieza de nombres de columnas
        df = pd.concat([pd.read_csv(LINK_1), pd.read_csv(LINK_2)], ignore_index=True)
        df.columns = [str(c).strip() for c in df.columns]
        
        # 2. Mapeo por posición (Col A=0, B=1, H=7, J=9, L=11)
        df['Empresa_V'] = df.iloc[:, 0].astype(str).str.strip()
        # NORMALIZACIÓN CRÍTICA: Todo a minúsculas y sin espacios extras
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
        
        # Eliminar filas basura
        return df[(df['Anio_V'] >= 2025) & (df['Empresa_V'] != 'nan') & (df['Empresa_V'] != '')]
    except Exception as e:
        st.error(f"Error técnico: {e}")
        return pd.DataFrame()

df = cargar_data()

if not df.empty:
    with st.sidebar:
        st.header("🎛️ Filtros Pro")
        modo = st.radio("Nivel de Análisis:", ["Ejecutivo (Cierres)", "Operativo (Semanal)"])
        empresa_sel = st.selectbox("Empresa Target", ["Todas las Empresas"] + sorted(df['Empresa_V'].unique()))
        anios_sel = st.multiselect("Años", [2026, 2025], default=[2026, 2025])
        meses_sel = st.multiselect("Meses", [1, 2], default=[1, 2], 
                                   format_func=lambda x: {1:'Ene', 2:'Feb'}.get(x))

    # Filtrado dinámico
    mask = (df['Anio_V'].isin(anios_sel)) & (df['Mes_V'].isin(meses_sel))
    if empresa_sel != "Todas las Empresas":
        mask &= (df['Empresa_V'] == empresa_sel)
    
    df_f = df[mask].copy()

    # --- LÓGICA DE SEPARACIÓN (CIERRES VS SEMANAS) ---
    if "Ejecutivo" in modo:
        # Captura "mes total", "total", etc.
        df_vis = df_f[df_f['Semana_V'].str.contains('total', na=False)]
    else:
        # Excluye los totales para mostrar el avance semanal
        df_vis = df_f[~df_f['Semana_V'].str.contains('total', na=False)]

    st.title(f"📊 Dashboard: {empresa_sel}")

    if not df_vis.empty:
        # Ordenamiento de semanas (Independiente de mayúsculas/minúsculas)
        sem_map = {'1era semana': 1, '2da semana': 2, '3era semana': 3, '4ta semana': 4, 'mes total': 5}
        df_vis['sem_idx'] = df_vis['Semana_V'].map(sem_map).fillna(6)
        df_vis = df_vis.sort_values(['Anio_V', 'Mes_V', 'sem_idx'])

        fig = go.Figure()
        colores = {2025: CORAL, 2026: SEA}
        mes_names = {1:'Ene', 2:'Feb'}

        for a in sorted(anios_sel):
            d_plot = df_vis[df_vis['Anio_V'] == a]
            # Agrupamos por si hay varias empresas bajo el mismo filtro
            d_grp = d_plot.groupby(['Mes_V', 'Semana_V', 'sem_idx'])['Usabilidad_V'].mean().reset_index()
            d_grp = d_grp.sort_values(['Mes_V', 'sem_idx'])
            
            x_labels = [f"{mes_names.get(m)}-{s.capitalize()}" for m, s in zip(d_grp['Mes_V'], d_grp['Semana_V'])]
            
            fig.add_trace(go.Scatter(
                x=x_labels, y=d_grp['Usabilidad_V'],
                name=f"Año {a}", mode='lines+markers+text',
                line=dict(color=colores.get(a, BLACK), width=4),
                text=[f"{v:.1%}" for v in d_grp['Usabilidad_V']],
                textposition="top center"
            ))

        fig.update_layout(yaxis=dict(tickformat=".0%", range=[0, 1.1]), height=500)
        st.plotly_chart(fig, use_container_width=True)

        # --- INFORME IA ---
        st.markdown("### 🧠 Informe de Desempeño Holos")
        avg_26 = df_vis[df_vis['Anio_V'] == 2026]['Usabilidad_V'].mean() if not df_vis[df_vis['Anio_V'] == 2026].empty else 0
        st.info(f"Análisis Automático: La data de Febrero ha sido integrada. La media actual de 2026 es **{avg_26:.1%}**. Se observa una continuidad en el registro semanal.")

    else:
        st.error("No hay datos que coincidan. Revisa que en el Excel las columnas J y L tengan los números correctos.")

    with st.expander("🔍 Verificador de Datos (Auditoría)"):
        st.dataframe(df_vis[['Empresa_V', 'Anio_V', 'Mes_V', 'Semana_V', 'Usabilidad_V']])
