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
        # Cargamos y limpiamos nombres de columnas
        df1 = pd.read_csv(LINK_1)
        df2 = pd.read_csv(LINK_2)
        df = pd.concat([df1, df2], ignore_index=True)
        df.columns = [str(c).strip() for c in df.columns]
        
        # Creación de DataFrame con nombres fijos para evitar el KeyError
        res = pd.DataFrame()
        res['Empresa'] = df.iloc[:, 0].astype(str).str.strip()
        res['Semana'] = df.iloc[:, 1].astype(str).str.strip()
        
        # COLUMNA G (Índice 7): % Usabilidad - Limpieza profunda
        def clean_percent(x):
            if pd.isna(x) or str(x).strip() == "": return None # Importante para no promediar ceros falsos
            try:
                val = float(str(x).replace('%', '').replace(',', '.'))
                return val/100 if val > 1.1 else val
            except: return None

        res['Usabilidad'] = df.iloc[:, 7].apply(clean_percent)
        res['Mes_N'] = pd.to_numeric(df.iloc[:, 9], errors='coerce')
        res['Anio_N'] = pd.to_numeric(df.iloc[:, 11], errors='coerce')
        
        # Filtramos filas sin datos esenciales
        return res.dropna(subset=['Anio_N', 'Mes_N', 'Usabilidad'])
    except Exception as e:
        st.error(f"Error técnico: {e}")
        return pd.DataFrame()

df = cargar_data()

if not df.empty:
    with st.sidebar:
        st.header("🎛️ Filtros")
        empresa_sel = st.selectbox("Empresa Target", ["Todas las Empresas"] + sorted(df['Empresa'].unique()))
        anios_sel = st.multiselect("Años", sorted(df['Anio_N'].unique().tolist(), reverse=True), default=[2026, 2025])
        
        m_map = {1:'Ene', 2:'Feb', 3:'Mar', 4:'Abr', 5:'May', 6:'Jun', 7:'Jul', 8:'Ago', 9:'Set', 10:'Oct', 11:'Nov', 12:'Dic'}
        meses_sel = st.multiselect("Meses", list(m_map.keys()), default=[1, 2], format_func=lambda x: m_map.get(x))

    # Filtrado lógico
    mask = (df['Anio_N'].isin(anios_sel)) & (df['Mes_N'].isin(meses_sel))
    if empresa_sel != "Todas las Empresas":
        mask &= (df['Empresa'] == empresa_sel)
    
    df_f = df[mask].copy()

    st.title(f"📊 Reporte de Usabilidad: {empresa_sel}")

    if not df_f.empty:
        # EL SECRETO DEL ORDEN: 1era < 2da < 3era < 4ta < Mes Total
        rank_map = {'1era semana': 1, '2da semana': 2, '3era semana': 3, '4ta semana': 4, 'mes total': 5}
        df_f['rank'] = df_f['Semana'].str.lower().map(rank_map).fillna(6)
        
        # Agrupamos por lo que realmente importa
        df_plot = df_f.groupby(['Anio_N', 'Mes_N', 'Semana', 'rank'])['Usabilidad'].mean().reset_index()
        df_plot = df_plot.sort_values(['Anio_N', 'Mes_N', 'rank'])
        df_plot['Etiqueta'] = df_plot.apply(lambda x: f"{m_map.get(x['Mes_N'])}-{x['Semana']}", axis=1)

        # Gráfico
        fig = go.Figure()
        colores = {2025: CORAL, 2026: SEA}

        for a in sorted(anios_sel):
            d_anio = df_plot[df_plot['Anio_N'] == a]
            if not d_anio.empty:
                fig.add_trace(go.Scatter(
                    x=d_anio['Etiqueta'], y=d_anio['Usabilidad'],
                    name=f"Año {int(a)}", mode='lines+markers+text',
                    text=[f"{v:.1%}" for v in d_anio['Usabilidad']],
                    textposition="top center",
                    line=dict(color=colores.get(a, BLACK), width=4),
                    connectgaps=True
                ))

        fig.update_layout(yaxis=dict(tickformat=".0%", range=[0, 1.1]), hovermode="x unified", height=500)
        st.plotly_chart(fig, use_container_width=True)

        # --- ANÁLISIS IA ---
        st.markdown("### 🧠 Informe de Desempeño Holos")
        try:
            df_2026 = df_plot[df_plot['Anio_N'] == 2026]
            if not df_2026.empty:
                ult_val = df_2026['Usabilidad'].iloc[-1]
                ult_lbl = df_2026['Etiqueta'].iloc[-1]
                st.success(f"**Diagnóstico:** Para **{ult_lbl}**, la usabilidad es de **{ult_val:.1%}**. Se observa una transición correcta entre los periodos de Enero y Febrero 2026.")
        except:
            pass

    with st.expander("📂 Detalle de registros encontrados"):
        # Mostramos solo las columnas que existen para evitar el KeyError
        st.dataframe(df_f[['Empresa', 'Anio_N', 'Mes_N', 'Semana', 'Usabilidad']].sort_values(['Anio_N', 'Mes_N', 'rank']))
else:
    st.warning("No se detectan datos. Verifica en tu Excel que las columnas J (Mes) y L (Año) tengan números (1, 2 y 2026).")
