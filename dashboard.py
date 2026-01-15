import streamlit as st
import pandas as pd
import plotly.graph_objects as go

# 1. Configuración y Estilo Celeste
st.set_page_config(page_title="Dashboard Holos", layout="wide")
st.markdown("<style>.stApp {background-color: #E3F2FD;}</style>", unsafe_allow_html=True)

def encontrar_columna(df, palabras_clave):
    for col in df.columns:
        for palabra in palabras_clave:
            if palabra.lower() in col.lower(): return col
    return None

@st.cache_data
def load_data():
    file_path = "A. Reporte de Usabilidad B2B 2023_2024_2025.xlsx - Detail39.csv"
    df = pd.read_csv(file_path)
    
    c_emp = encontrar_columna(df, ['Nombre', 'Empresa'])
    c_usa = encontrar_columna(df, ['% Usabilidad', 'Engagement'])
    c_met = encontrar_columna(df, ['Meta en %', 'Meta %'])
    c_mes = encontrar_columna(df, ['Inicio del Mes', 'Mes'])
    c_ani = encontrar_columna(df, ['Inicio de Año', 'Año'])
    c_sem = encontrar_columna(df, ['Semana'])

    def limpiar_pct(valor):
        if pd.isna(valor): return 0.0
        s = str(valor).replace('%', '').replace(',', '.').strip()
        try:
            n = float(s)
            return n / 100.0 if n > 1.0 else n
        except: return 0.0

    df['Usabilidad_Limpia'] = df[c_usa].apply(limpiar_pct)
    df['Meta_Limpia'] = df[c_met].apply(limpiar_pct)
    df['Anio_Limpio'] = pd.to_numeric(df[c_ani], errors='coerce').fillna(0).astype(int)
    df['Mes_Limpio'] = pd.to_numeric(df[c_mes], errors='coerce').fillna(0).astype(int)
    df['Empresa_Limpia'] = df[c_emp].astype(str).str.strip()

    if c_sem:
        df = df[df[c_sem].astype(str).str.contains('total', case=False, na=False)].copy()
    return df

try:
    df = load_data()

    # --- ENCABEZADO CON LOGO E INDICADORES CIRCULARES ---
    col_logo, col_tit, col_g1, col_g2 = st.columns([1, 2, 1, 1])
    
    with col_logo:
        st.image("https://www.holos.club/_next/static/media/logo-black.68e7f8e7.svg", width=130)
    
    with col_tit:
        st.title("Reporte de Usabilidad")

    # Filtros Sidebar
    with st.sidebar:
        st.header("Filtros")
        lista_empresas = ["Todas las Empresas"] + sorted(df['Empresa_Limpia'].unique().tolist())
        emp_sel = st.selectbox("Selecciona Empresa", lista_empresas)
        anios_sel = st.multiselect("Años", sorted(df['Anio_Limpio'].unique()), default=[2024, 2025])
        
        meses_map = {1:'Ene', 2:'Feb', 3:'Mar', 4:'Abr', 5:'May', 6:'Jun', 7:'Jul', 8:'Ago', 9:'Set', 10:'Oct', 11:'Nov', 12:'Dic'}
        meses_sel = st.multiselect("Meses", sorted(meses_map.keys()), default=sorted(meses_map.keys()), format_func=lambda x: meses_map[x])

    # Lógica de Datos
    mask_base = (df['Anio_Limpio'].isin(anios_sel)) & (df['Mes_Limpio'].isin(meses_sel))
    df_filtrado = df[mask_base].copy()

    if emp_sel == "Todas las Empresas":
        df_plot = df_filtrado.groupby(['Anio_Limpio', 'Mes_Limpio']).agg({'Usabilidad_Limpia': 'mean', 'Meta_Limpia': 'mean'}).reset_index()
        
        # --- CÁLCULO DE PROMEDIOS ACUMULADOS PARA LOS CÍRCULOS ---
        def crear_circulo(anio, color):
            val = df_filtrado[df_filtrado['Anio_Limpio'] == anio]['Usabilidad_Limpia'].mean()
            fig_g = go.Figure(go.Indicator(
                mode = "gauge+number",
                value = val * 100,
                number = {'suffix': "%", 'font': {'size': 20}},
                title = {'text': f"Promedio {anio}", 'font': {'size': 14}},
                gauge = {
                    'axis': {'range': [0, 100]},
                    'bar': {'color': color},
                    'bgcolor': "white",
                    'borderwidth': 2,
                    'bordercolor': "gray",
                }
            ))
            fig_g.update_layout(height=150, margin=dict(l=20, r=20, t=30, b=20), paper_bgcolor='rgba(0,0,0,0)')
            return fig_g

        with col_g1: st.plotly_chart(crear_circulo(2024, "#1f77b4"), use_container_width=True)
        with col_g2: st.plotly_chart(crear_circulo(2025, "#FF4B4B"), use_container_width=True)

    else:
        df_filtrado = df_filtrado[df_filtrado['Empresa_Limpia'] == emp_sel]
        df_plot = df_filtrado.sort_values(['Anio_Limpio', 'Mes_Limpio'])

    # --- GRÁFICO PRINCIPAL ---
    if not df_plot.empty:
        fig = go.Figure()
        for anio in anios_sel:
            d = df_plot[df_plot['Anio_Limpio'] == anio]
            if not d.empty:
                mx = [meses_map.get(m) for m in d['Mes_Limpio']]
                fig.add_trace(go.Bar(x=mx, y=d['Usabilidad_Limpia'], name=f"Real {anio}", text=[f"{v:.1%}" for v in d['Usabilidad_Limpia']], textposition='outside'))
                fig.add_trace(go.Scatter(x=mx, y=d['Meta_Limpia'], name=f"Meta {anio}", mode='lines+markers', line=dict(dash='dash')))
        
        fig.update_layout(paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='white', yaxis=dict(tickformat=".0%", range=[0, 1.2]), barmode='group')
        st.plotly_chart(fig, use_container_width=True)

        # --- ANÁLISIS DINÁMICO ---
        st.markdown("---")
        st.subheader(f"📝 Análisis de Desempeño")
        
        # Lógica de análisis (semestres y tendencias)
        def analizar(data_df):
            texto = ""
            for a in anios_sel:
                d_anio = data_df[data_df['Anio_Limpio'] == a]
                if not d_anio.empty:
                    s1 = d_anio[d_anio['Mes_Limpio'] <= 6]['Usabilidad_Limpia'].mean()
                    s2 = d_anio[d_anio['Mes_Limpio'] > 6]['Usabilidad_Limpia'].mean()
                    mejor = "1er Semestre" if s1 > s2 else "2do Semestre"
                    texto += f"* **En {a}:** Mayor performance en el **{mejor}** ({max(s1,s2):.1%}). "
            return texto

        st.info(analizar(df_filtrado))

    else:
        st.warning("No hay datos disponibles.")

except Exception as e:
    st.error(f"Error: {e}")