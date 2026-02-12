import streamlit as st
import pandas as pd
import plotly.graph_objects as go

# 1. Configuración de pantalla
st.set_page_config(page_title="Holos | BI Dashboard", layout="wide")

LINK_1 = "https://docs.google.com/spreadsheets/d/e/2PACX-1vSWiXR7BLxwzX2wtD_uF59pvxtus8BL5iqgymKSh2-Llwt6smOJzR7ROUxICr57DA/pub?gid=1638907402&single=true&output=csv"
LINK_2 = "https://docs.google.com/spreadsheets/d/e/2PACX-1vSWiXR7BLxwzX2wtD_uF59pvxtus8BL5iqgymKSh2-Llwt6smOJzR7ROUxICr57DA/pub?gid=1341962834&single=true&output=csv"

# Colores Corporativos
SKY, LEAF, SEA, CORAL, BLACK = "#D1E9F6", "#F1FB8C", "#A9C1F5", "#FF9F86", "#000000"

@st.cache_data(ttl=5)
def cargar_data():
    try:
        df = pd.concat([pd.read_csv(LINK_1), pd.read_csv(LINK_2)], ignore_index=True)
        df.columns = [str(c).strip() for c in df.columns]
        
        # Mapeo por posición para ignorar errores de tildes o nombres de columnas
        df['Empresa_V'] = df.iloc[:, 0].astype(str).str.strip()
        df['Semana_V'] = df.iloc[:, 1].astype(str).str.strip().str.lower() # Todo a minúsculas para comparar
        df['Mes_V'] = pd.to_numeric(df.iloc[:, 9], errors='coerce').fillna(0).astype(int)
        df['Anio_V'] = pd.to_numeric(df.iloc[:, 11], errors='coerce').fillna(0).astype(int)
        
        def limpiar_pct(val):
            try:
                s = str(val).replace('%', '').replace(',', '.').strip()
                n = float(s)
                return n / 100.0 if n > 1.1 else n
            except: return 0.0
        
        df['Usabilidad_V'] = df.iloc[:, 7].apply(limpiar_pct)
        # Filtro de seguridad
        return df[(df['Anio_V'] >= 2025) & (df['Empresa_V'] != 'nan')]
    except Exception as e:
        st.error(f"Error en carga: {e}")
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

    # Filtrado base
    mask = (df['Anio_V'].isin(anios_sel)) & (df['Mes_V'].isin(meses_sel))
    if empresa_sel != "Todas las Empresas":
        mask &= (df['Empresa_V'] == empresa_sel)
    
    df_f = df[mask].copy()

    # --- LÓGICA DE CIERRE EJECUTIVO (CORREGIDO PARA ENERO) ---
    # Buscamos cualquier fila que diga "total" sin importar mayúsculas
    if "Ejecutivo" in modo:
        df_vis = df_f[df_f['Semana_V'].str.contains('total', na=False)]
    else:
        # --- LÓGICA SEMANAL (CORREGIDO PARA FEBRERO) ---
        df_vis = df_f[~df_f['Semana_V'].str.contains('total', na=False)]

    st.title(f"📊 Dashboard: {empresa_sel}")

    if not df_vis.empty:
        # Ordenar semanas: 1era, 2da, 3era, 4ta
        sem_map = {'1era semana': 1, '2da semana': 2, '3era semana': 3, '4ta semana': 4}
        df_vis['sem_idx'] = df_vis['Semana_V'].map(sem_map).fillna(5)
        df_vis = df_vis.sort_values(['Anio_V', 'Mes_V', 'sem_idx'])

        fig = go.Figure()
        mes_names = {1:'Ene', 2:'Feb'}
        colores = {2025: CORAL, 2026: SEA}

        for a in sorted(anios_sel):
            d_plot = df_vis[df_vis['Anio_V'] == a]
            # Agrupamos por si hay varias empresas, para ver el promedio total
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

        fig.update_layout(yaxis=dict(tickformat=".0%", range=[0, 1.1]), height=450)
        st.plotly_chart(fig, use_container_width=True)

        # --- INFORME IA (RECUPERADO) ---
        st.markdown("### 🧠 Informe de Desempeño Holos")
        st.info(f"Análisis: Se han detectado {len(df_vis)} registros válidos para el periodo seleccionado. "
                f"La usabilidad de 2026 en este corte es del {df_vis[df_vis['Anio_V']==2026]['Usabilidad_V'].mean():.1%}")

    else:
        st.warning("⚠️ No se encontró data de 'Mes total' para Enero en el modo Ejecutivo o faltan datos de Febrero.")

    with st.expander("🔍 Auditoría de datos (Si ves esto vacío, revisa el Excel)"):
        st.write("Filas detectadas para los filtros seleccionados:")
        st.dataframe(df_vis[['Empresa_V', 'Anio_V', 'Mes_V', 'Semana_V', 'Usabilidad_V']])
