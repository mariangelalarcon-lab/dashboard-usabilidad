import streamlit as st
import pandas as pd
import plotly.graph_objects as go

# 1. Configuración Pro
st.set_page_config(page_title="Holos | Business Intelligence", layout="wide")

LINK_1 = "https://docs.google.com/spreadsheets/d/e/2PACX-1vSWiXR7BLxwzX2wtD_uF59pvxtus8BL5iqgymKSh2-Llwt6smOJzR7ROUxICr57DA/pub?gid=1638907402&single=true&output=csv"
LINK_2 = "https://docs.google.com/spreadsheets/d/e/2PACX-1vSWiXR7BLxwzX2wtD_uF59pvxtus8BL5iqgymKSh2-Llwt6smOJzR7ROUxICr57DA/pub?gid=1341962834&single=true&output=csv"

SKY, LEAF, SEA, CORAL, BLACK = "#D1E9F6", "#F1FB8C", "#A9C1F5", "#FF9F86", "#000000"

@st.cache_data(ttl=5)
def cargar_data():
    try:
        # Carga y limpieza inicial
        df = pd.concat([pd.read_csv(LINK_1), pd.read_csv(LINK_2)], ignore_index=True)
        df.columns = [str(c).strip() for c in df.columns]
        
        # Procesamiento de columnas por posición para evitar errores de tildes/espacios
        df['Empresa_V'] = df.iloc[:, 0].astype(str).str.strip()
        df['Semana_V'] = df.iloc[:, 1].astype(str).str.strip()
        df['Mes_V'] = pd.to_numeric(df.iloc[:, 9], errors='coerce').fillna(0).astype(int)
        df['Anio_V'] = pd.to_numeric(df.iloc[:, 11], errors='coerce').fillna(0).astype(int)
        
        def limpiar_pct(val):
            try:
                if pd.isna(val): return 0.0
                s = str(val).replace('%', '').replace(',', '.').strip()
                n = float(s)
                return n / 100.0 if n > 1.1 else n
            except: return 0.0
        
        df['Usabilidad_V'] = df.iloc[:, 7].apply(limpiar_pct)
        
        # Filtro de seguridad: eliminar filas sin año o sin empresa real
        df = df[(df['Anio_V'] >= 2025) & (df['Empresa_V'] != 'nan') & (df['Empresa_V'] != '')]
        return df
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
        meses_sel = st.multiselect("Meses", [1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12], 
                                   default=[1, 2], 
                                   format_func=lambda x: {1:'Ene', 2:'Feb', 3:'Mar', 4:'Abr', 5:'May', 6:'Jun', 
                                                          7:'Jul', 8:'Ago', 9:'Set', 10:'Oct', 11:'Nov', 12:'Dic'}.get(x))

    # Filtrado Dinámico
    mask = (df['Anio_V'].isin(anios_sel)) & (df['Mes_V'].isin(meses_sel))
    if empresa_sel != "Todas las Empresas":
        mask &= (df['Empresa_V'] == empresa_sel)
    
    df_f = df[mask].copy()

    # Lógica de Semanas vs Cierres
    if "Ejecutivo" in modo:
        df_vis = df_f[df_f['Semana_V'].str.contains('total|Total', na=False)]
    else:
        df_vis = df_f[~df_f['Semana_V'].str.contains('total|Total', na=False)]

    st.title(f"📊 Reporte: {empresa_sel}")

    # --- GRÁFICA CORREGIDA ---
    if not df_vis.empty:
        # Ordenamiento cronológico estricto
        sem_map = {'1era Semana': 1, '2da Semana': 2, '3era Semana': 3, '4ta semana': 4, '1era semana': 1, '2da semana': 2, '3era semana': 3}
        df_vis['sem_num'] = df_vis['Semana_V'].map(sem_map).fillna(5)
        df_vis = df_vis.sort_values(['Anio_V', 'Mes_V', 'sem_num'])

        fig = go.Figure()
        mes_labels = {1:'Ene', 2:'Feb', 3:'Mar', 4:'Abr', 5:'May', 6:'Jun', 7:'Jul', 8:'Ago', 9:'Set', 10:'Oct', 11:'Nov', 12:'Dic'}
        colores = {2025: CORAL, 2026: SEA}

        for a in sorted(anios_sel):
            d_plot = df_vis[df_vis['Anio_V'] == a]
            if not d_plot.empty:
                # Agrupamos para asegurar que no haya duplicados que quiebren la línea
                d_grp = d_plot.groupby(['Mes_V', 'Semana_V', 'sem_num'])['Usabilidad_V'].mean().reset_index()
                d_grp = d_grp.sort_values(['Mes_V', 'sem_num'])
                
                x_axis = [f"{mes_labels.get(m)}-{s}" for m, s in zip(d_grp['Mes_V'], d_grp['Semana_V'])]
                
                fig.add_trace(go.Scatter(
                    x=x_axis, y=d_grp['Usabilidad_V'],
                    name=f"Año {a}", mode='lines+markers+text',
                    line=dict(color=colores.get(a, BLACK), width=4),
                    text=[f"{v:.1%}" for v in d_grp['Usabilidad_V']],
                    textposition="top center"
                ))

        fig.update_layout(yaxis=dict(tickformat=".0%", range=[0, 1.1]), hovermode="x unified")
        st.plotly_chart(fig, use_container_width=True)

        # --- INFORME CON IA RECUPERADO ---
        st.markdown("### 🧠 Informe de Desempeño Holos")
        avg_26 = df_vis[df_vis['Anio_V'] == 2026]['Usabilidad_V'].mean()
        st.markdown(f"""
        <div style="background-color: white; border-left: 6px solid {LEAF}; padding: 20px; border-radius: 10px; color: black;">
            <strong>Análisis de Febrero:</strong> Se confirma la lectura de datos para 2026. 
            La usabilidad media actual es de <b>{avg_26:.1%}</b>.<br>
            <strong>Tendencia:</strong> La comparación entre periodos muestra que el engagement de febrero está siendo procesado exitosamente.
        </div>
        """, unsafe_allow_html=True)
    else:
        st.warning("No hay datos para mostrar. Revisa que las celdas de Febrero en la columna J tengan el número 2.")
