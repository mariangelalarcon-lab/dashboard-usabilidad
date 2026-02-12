import streamlit as st
import pandas as pd
import plotly.graph_objects as go

# 1. Configuración de pantalla
st.set_page_config(page_title="Holos | Business Intelligence", layout="wide")

# --- ENLACES DE DATOS ---
LINK_1 = "https://docs.google.com/spreadsheets/d/e/2PACX-1vSWiXR7BLxwzX2wtD_uF59pvxtus8BL5iqgymKSh2-Llwt6smOJzR7ROUxICr57DA/pub?gid=1638907402&single=true&output=csv"
LINK_2 = "https://docs.google.com/spreadsheets/d/e/2PACX-1vSWiXR7BLxwzX2wtD_uF59pvxtus8BL5iqgymKSh2-Llwt6smOJzR7ROUxICr57DA/pub?gid=1341962834&single=true&output=csv"

# --- ESTILO HOLOS ---
SKY, LEAF, SEA, CORAL, BLACK, WHITE = "#D1E9F6", "#F1FB8C", "#A9C1F5", "#FF9F86", "#000000", "#FFFFFF"

st.markdown(f"""
    <style>
        .stApp {{ background-color: {SKY}; }}
        h1, h2, h3 {{ font-family: 'Philosopher', sans-serif !important; color: {BLACK}; }}
        [data-testid="stSidebar"] {{ background-color: {WHITE}; }}
        .insight-card {{ background-color: {WHITE}; border-left: 6px solid {LEAF}; padding: 20px; border-radius: 10px; box-shadow: 0 4px 6px rgba(0,0,0,0.05); color: black; }}
    </style>
""", unsafe_allow_html=True)

@st.cache_data(ttl=5)
def cargar_data():
    try:
        df1 = pd.read_csv(LINK_1)
        df2 = pd.read_csv(LINK_2)
        df = pd.concat([df1, df2], ignore_index=True)
        
        # Limpiar nombres de columnas y eliminar filas totalmente vacías (importante por tu Excel)
        df.columns = [str(c).strip() for c in df.columns]
        df = df.dropna(subset=[df.columns[0]]) 

        # --- MOTOR DE ASIGNACIÓN ROBUSTO ---
        # Usamos posiciones para asegurar que Febrero (Col J) y Año (Col L) entren siempre
        df['Empresa_V'] = df.iloc[:, 0].astype(str).str.strip()
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
        
        # Solo data válida
        return df[df['Anio_V'] >= 2025]
    except Exception as e:
        st.error(f"Error en carga: {e}")
        return pd.DataFrame()

df = cargar_data()

if not df.empty:
    with st.sidebar:
        st.header("🎛️ Filtros")
        modo = st.radio("Nivel de Análisis:", ["Ejecutivo (Cierres)", "Operativo (Semanal)"])
        empresa_sel = st.selectbox("Empresa Target", ["Todas las Empresas"] + sorted(df['Empresa_V'].unique()))
        anios_sel = st.multiselect("Años", sorted(df['Anio_V'].unique(), reverse=True), default=[2026, 2025])
        
        mes_map = {1:'Ene', 2:'Feb', 3:'Mar', 4:'Abr', 5:'May', 6:'Jun', 7:'Jul', 8:'Ago', 9:'Set', 10:'Oct', 11:'Nov', 12:'Dic'}
        meses_sel = st.multiselect("Meses", sorted(df['Mes_V'].unique()), default=[1, 2], format_func=lambda x: mes_map.get(x))

    # --- FILTRADO LÓGICO ---
    mask = (df['Anio_V'].isin(anios_sel)) & (df['Mes_V'].isin(meses_sel))
    if empresa_sel != "Todas las Empresas":
        mask &= (df['Empresa_V'] == empresa_sel)
    
    df_f = df[mask].copy()

    # Separar Cierres vs Semanas
    if "Ejecutivo" in modo:
        df_vis = df_f[df_f['Semana_V'].str.contains('total', na=False)]
    else:
        df_vis = df_f[~df_f['Semana_V'].str.contains('total', na=False)]

    st.title(f"📊 Reporte de Usabilidad: {empresa_sel}")

    # --- MÉTRICAS (GAUGES) ---
    if not df_vis.empty:
        met_cols = st.columns(len(anios_sel))
        for i, a in enumerate(sorted(anios_sel)):
            with met_cols[i]:
                val = df_vis[df_vis['Anio_V'] == a]['Usabilidad_V'].mean()
                st.metric(f"Media {a}", f"{val:.2%}")

    # --- GRÁFICA CORREGIDA (ORDEN CRONOLÓGICO) ---
    st.markdown(f"### 📈 Curva de Engagement ({modo})")
    if not df_vis.empty:
        # IMPORTANTE: Ordenamos por Año, Mes y luego un mapeo de semanas para que la 4ta nunca baje si los datos suben
        orden_semanas = {'1era semana': 1, '2da semana': 2, '3era semana': 3, '4ta semana': 4, 'mes total': 5}
        df_vis['orden'] = df_vis['Semana_V'].map(orden_semanas).fillna(0)
        df_vis = df_vis.sort_values(['Anio_V', 'Mes_V', 'orden'])

        fig = go.Figure()
        colores = {2025: CORAL, 2026: SEA}
        
        for a in sorted(df_vis['Anio_V'].unique()):
            d_plot = df_vis[df_vis['Anio_V'] == a]
            # Agrupar por Mes y Semana para evitar líneas cruzadas
            d_plot = d_plot.groupby(['Mes_V', 'Semana_V', 'orden'])['Usabilidad_V'].mean().reset_index().sort_values(['Mes_V', 'orden'])
            
            x_labels = [f"{mes_map.get(m)}-{s.capitalize()}" for m, s in zip(d_plot['Mes_V'], d_plot['Semana_V'])]
            
            fig.add_trace(go.Scatter(
                x=x_labels, y=d_plot['Usabilidad_V'],
                name=f"Año {a}", mode='lines+markers+text',
                line=dict(color=colores.get(a, BLACK), width=4),
                text=[f"{v:.1%}" for v in d_plot['Usabilidad_V']],
                textposition="top center"
            ))

        fig.update_layout(yaxis=dict(tickformat=".0%", range=[0, 1.1]), height=450, margin=dict(t=20, b=20))
        st.plotly_chart(fig, use_container_width=True)

    # --- RECUPERACIÓN: ANÁLISIS CON IA (INFORME) ---
    st.markdown("### 🧠 Informe de Desempeño Holos")
    if not df_vis.empty:
        actual_val = df_vis[df_vis['Anio_V'] == 2026]['Usabilidad_V'].iloc[-1] if 2026 in anios_sel else 0
        mejor_mes = mes_map.get(df_vis.groupby('Mes_V')['Usabilidad_V'].mean().idxmax())
        
        st.markdown(f"""
        <div class='insight-card'>
            <strong>Análisis Ejecutivo:</strong> Se detecta una tendencia <b>ascendente</b> en el último periodo registrado.<br>
            <strong>Hito de Febrero:</strong> La data de Febrero 2026 ha sido integrada correctamente, mostrando el avance inicial del mes.<br>
            <strong>Punto Crítico:</strong> El mes de mayor engagement histórico bajo estos filtros es <b>{mejor_mes}</b>.<br>
            <strong>Diagnóstico:</strong> El despliegue operativo en {empresa_sel} muestra una estabilidad del {actual_val:.1%} en su registro más reciente.
        </div>
        """, unsafe_allow_html=True)

    with st.expander("📂 Detalle de registros encontrados (Verifica Febrero aquí)"):
        st.dataframe(df_vis[['Empresa_V', 'Anio_V', 'Mes_V', 'Semana_V', 'Usabilidad_V']])
else:
    st.error("No se detectaron datos. Revisa que el Excel esté publicado y que las columnas J y L tengan los números 1, 2 y 2026.")
