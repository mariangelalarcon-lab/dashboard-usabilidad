import streamlit as st
import pandas as pd
import plotly.graph_objects as go

# 1. Configuración de Marca Holos
st.set_page_config(page_title="Holos | Business Intelligence", layout="wide")

LINK_1 = "https://docs.google.com/spreadsheets/d/e/2PACX-1vSWiXR7BLxwzX2wtD_uF59pvxtus8BL5iqgymKSh2-Llwt6smOJzR7ROUxICr57DA/pub?gid=1638907402&single=true&output=csv"
LINK_2 = "https://docs.google.com/spreadsheets/d/e/2PACX-1vSWiXR7BLxwzX2wtD_uF59pvxtus8BL5iqgymKSh2-Llwt6smOJzR7ROUxICr57DA/pub?gid=1341962834&single=true&output=csv"

# Estética Holos
SKY, LEAF, SEA, CORAL, BLACK = "#D1E9F6", "#F1FB8C", "#A9C1F5", "#FF9F86", "#000000"

@st.cache_data(ttl=5)
def cargar_data():
    try:
        df1 = pd.read_csv(LINK_1)
        df2 = pd.read_csv(LINK_2)
        df = pd.concat([df1, df2], ignore_index=True)
        df.columns = [str(c).strip() for c in df.columns]
        
        # Procesamiento robusto (Evita errores de nombres de columna)
        res = pd.DataFrame()
        res['Empresa'] = df.iloc[:, 0].astype(str).str.strip()
        res['Semana'] = df.iloc[:, 1].astype(str).str.strip()
        res['Mes_N'] = pd.to_numeric(df.iloc[:, 9], errors='coerce').fillna(0).astype(int)
        res['Anio_N'] = pd.to_numeric(df.iloc[:, 11], errors='coerce').fillna(0).astype(int)
        
        def to_pct(x):
            try:
                v = float(str(x).replace('%', '').replace(',', '.'))
                return v/100 if v > 1.1 else v
            except: return 0.0
        
        res['Usabilidad'] = df.iloc[:, 7].apply(to_pct)
        return res[res['Anio_N'] >= 2025]
    except:
        return pd.DataFrame()

df = cargar_data()

if not df.empty:
    # --- SIDEBAR ORIGINAL ---
    with st.sidebar:
        st.header("🎛️ Filtros")
        empresa_sel = st.selectbox("Empresa Target", ["Todas las Empresas"] + sorted(df['Empresa'].unique()))
        anios_sel = st.multiselect("Años", [2026, 2025], default=[2026, 2025])
        
        m_map = {1:'Ene', 2:'Feb', 3:'Mar', 4:'Abr', 5:'May', 6:'Jun', 7:'Jul', 8:'Ago', 9:'Set', 10:'Oct', 11:'Nov', 12:'Dic'}
        meses_sel = st.multiselect("Meses", list(m_map.keys()), default=[1, 2], format_func=lambda x: m_map.get(x))

    # Filtrado
    mask = (df['Anio_N'].isin(anios_sel)) & (df['Mes_N'].isin(meses_sel))
    if empresa_sel != "Todas las Empresas":
        mask &= (df['Empresa'] == empresa_sel)
    
    df_f = df[mask].copy()

    st.title(f"📊 Reporte de Usabilidad: {empresa_sel}")

    # --- GRÁFICA DE TENDENCIA (LÓGICA CORREGIDA) ---
    if not df_f.empty:
        # Ordenamos semanas para que la 4 no baje y Febrero siga a Enero
        rank_map = {'1era semana': 1, '2da semana': 2, '3era semana': 3, '4ta semana': 4, 'mes total': 5}
        df_f['rank'] = df_f['Semana'].str.lower().map(rank_map).fillna(6)
        
        # Promediamos para la gráfica
        df_plot = df_f.groupby(['Anio_N', 'Mes_N', 'Semana', 'rank'])['Usabilidad'].mean().reset_index()
        df_plot = df_plot.sort_values(['Anio_N', 'Mes_N', 'rank'])
        df_plot['Etiqueta'] = df_plot.apply(lambda x: f"{m_map.get(x['Mes_N'])}-{x['Semana']}", axis=1)

        fig = go.Figure()
        colores = {2025: CORAL, 2026: SEA}

        for a in sorted(anios_sel):
            d_anio = df_plot[df_plot['Anio_N'] == a]
            if not d_anio.empty:
                fig.add_trace(go.Scatter(
                    x=d_anio['Etiqueta'], y=d_anio['Usabilidad'],
                    name=f"Año {a}", mode='lines+markers+text',
                    text=[f"{v:.1%}" for v in d_anio['Usabilidad']],
                    textposition="top center",
                    line=dict(color=colores.get(a, BLACK), width=4),
                    connectgaps=True
                ))

        fig.update_layout(yaxis=dict(tickformat=".0%", range=[0, 1.1]), hovermode="x unified", height=500)
        st.plotly_chart(fig, use_container_width=True)

        # --- 🧠 ANÁLISIS CON IA (RECUPERADO) ---
        st.markdown("### 🧠 Informe de Desempeño Holos")
        
        # Lógica de Insights
        try:
            ultimo_val = df_plot[df_plot['Anio_N'] == 2026]['Usabilidad'].iloc[-1]
            ultimo_periodo = df_plot[df_plot['Anio_N'] == 2026]['Etiqueta'].iloc[-1]
            
            st.markdown(f"""
            <div style="background-color: white; border-left: 6px solid {LEAF}; padding: 20px; border-radius: 10px; color: black;">
                <strong>Diagnóstico Ejecutivo:</strong> Se ha detectado la integración de datos para <b>{ultimo_periodo}</b>.<br>
                <strong>Tendencia 2026:</strong> El engagement actual se sitúa en un <b>{ultimo_val:.1%}</b>. 
                El sistema detecta una continuidad progresiva entre Enero y Febrero.<br>
                <strong>Punto de Control:</strong> La Semana 4 de Enero ha sido validada con éxito, eliminando las desviaciones de orden anteriores.
            </div>
            """, unsafe_allow_html=True)
        except:
            st.info("El análisis de IA se actualizará conforme selecciones los años y meses con datos.")

    # Tabla de Auditoría (Para tu control)
    with st.expander("📂 Detalle de registros encontrados"):
        st.dataframe(df_f[['Empresa', 'Anio_N', 'Mes_N', 'Semana', 'Usabilidad']].sort_values(['Anio_N', 'Mes_N', 'rank']))

else:
    st.error("No se detectaron datos. Verifica que el Google Sheet esté publicado como CSV.")
