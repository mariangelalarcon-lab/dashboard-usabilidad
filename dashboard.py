import streamlit as st
import pandas as pd
import plotly.graph_objects as go
import os

# 1. Configuración de página
st.set_page_config(page_title="Reporte de Usabilidad Holos", layout="wide")

# ESTILO: Fondo celeste, fuentes Philosopher y transparencia total
st.markdown("""
    <link href="https://fonts.googleapis.com/css2?family=Philosopher:wght@400;700&display=swap" rel="stylesheet">
    <style>
        * { font-family: 'Philosopher', sans-serif !important; }
        .stApp { background-color: #D1E9F6; }
        .stSelectbox, .stMultiSelect { background-color: white; border-radius: 8px; }
        h1 { color: #000000; font-weight: 700; font-size: 3.5rem !important; margin-bottom: 0px; }
        [data-testid="stSidebar"] { background-color: #FFFFFF; }
        .stPlotlyChart { background-color: transparent !important; }
    </style>
""", unsafe_allow_html=True)

def encontrar_columna(df, palabras_clave):
    for col in df.columns:
        for palabra in palabras_clave:
            if palabra.lower() in col.lower(): return col
    return None

@st.cache_data
def load_data():
    archivos_csv = [f for f in os.listdir('.') if f.endswith('.csv')]
    if not archivos_csv: return pd.DataFrame()
    lista_df = [pd.read_csv(f) for f in archivos_csv]
    df = pd.concat(lista_df, ignore_index=True)
    
    c_emp = encontrar_columna(df, ['Nombre', 'Empresa'])
    c_usa = encontrar_columna(df, ['% Usabilidad', 'Engagement'])
    c_mes = encontrar_columna(df, ['Inicio del Mes', 'Mes'])
    c_ani = encontrar_columna(df, ['Inicio de Año', 'Año'])
    c_sem = encontrar_columna(df, ['Semana', 'Desglose']) 

    def limpiar_pct(row):
        valor = row[c_usa]
        empresa = str(row[c_emp]).lower()
        if pd.isna(valor): return 0.0
        s = str(valor).replace('%', '').replace(',', '.').strip()
        try:
            n = float(s)
            if "cardif" in empresa or "scotiabank" in empresa:
                return n / 10000.0 if n > 1.0 else n / 100.0
            return n / 100.0 if n > 1.0 else n
        except: return 0.0

    df['Usabilidad_Limpia'] = df.apply(limpiar_pct, axis=1)
    df['Anio_Limpio'] = pd.to_numeric(df[c_ani], errors='coerce').fillna(0).astype(int)
    df = df[df['Anio_Limpio'] > 2020].copy()
    df['Mes_Limpio'] = pd.to_numeric(df[c_mes], errors='coerce').fillna(0).astype(int)
    df['Empresa_Limpia'] = df[c_emp].astype(str).str.strip()
    df['Semana_Filtro'] = df[c_sem].astype(str).str.strip() if c_sem else "Mes Total"
    return df

try:
    df = load_data()
    if df.empty:
        st.stop()

    # --- ENCABEZADO ---
    col_tit, col_espacio, col_logo = st.columns([3, 1, 0.6])
    with col_tit:
        st.markdown("<h1>Reporte de Usabilidad</h1>", unsafe_allow_html=True)
    with col_logo:
        logo_path = "image_e57c24.png" if os.path.exists("image_e57c24.png") else "logo.png"
        if os.path.exists(logo_path):
            st.image(logo_path, width=150)

    st.markdown("---")

    # --- COLORES ACTUALIZADOS ---
    colores = {2024: "#F1FB8C", 2025: "#FF9F86", 2026: "#A9C1F5"}
    metas = {2024: 0.35, 2025: 0.40, 2026: 0.45} # Metas de ejemplo ajustables

    # --- INDICADORES CIRCULARES ---
    col_g1, col_g2, col_g3 = st.columns(3)

    # --- SIDEBAR ---
    with st.sidebar:
        st.markdown("### ⚙️ Filtros de Reporte")
        empresas_unicas = sorted([e for e in df['Empresa_Limpia'].unique() if e != 'nan'])
        emp_sel = st.selectbox("Seleccionar Empresa", ["Todas las Empresas"] + empresas_unicas)
        anios_sel = st.multiselect("Años a comparar", sorted(df['Anio_Limpio'].unique()), default=sorted(df['Anio_Limpio'].unique()))
        
        meses_map = {1:'Ene', 2:'Feb', 3:'Mar', 4:'Abr', 5:'May', 6:'Jun', 7:'Jul', 8:'Ago', 9:'Set', 10:'Oct', 11:'Nov', 12:'Dic'}
        meses_sel = st.multiselect("Meses", sorted(meses_map.keys()), default=sorted(meses_map.keys()), format_func=lambda x: meses_map[x])

        st.markdown("---")
        opciones_raw = sorted(df['Semana_Filtro'].unique().tolist())
        opciones_sin_total = [opt for opt in opciones_raw if "total" not in opt.lower()]
        seleccion_vista = st.selectbox("Detalle Temporal", ["Mes Total"] + opciones_sin_total)

    def crear_gauge_grande(anio, color, key):
        data_a = df[df['Anio_Limpio'] == anio]
        if emp_sel != "Todas las Empresas":
            data_a = data_a[data_a['Empresa_Limpia'] == emp_sel]
        val = data_a['Usabilidad_Limpia'].mean()
        if pd.isna(val) or val == 0: return
        
        fig = go.Figure(go.Indicator(
            mode="gauge+number", value=val*100,
            number={'suffix': "%", 'font': {'size': 45, 'color': '#000000'}, 'valueformat':'.1f'},
            title={'text': str(anio), 'font': {'size': 30, 'color': '#000000'}},
            gauge={'axis': {'range': [0, 100], 'tickfont': {'size': 14}}, 
                   'bar': {'color': color},
                   'bgcolor': "rgba(255,255,255,0.2)",
                   'bordercolor': "black"}
        ))
        fig.update_layout(height=280, margin=dict(l=20, r=20, t=80, b=0), paper_bgcolor='rgba(0,0,0,0)')
        st.plotly_chart(fig, use_container_width=True, key=key)

    with col_g1:
        if 2024 in anios_sel: crear_gauge_grande(2024, colores[2024], "c24")
    with col_g2:
        if 2025 in anios_sel: crear_gauge_grande(2025, colores[2025], "c25")
    with col_g3:
        if 2026 in anios_sel: crear_gauge_grande(2026, colores[2026], "c26")

    # --- LÓGICA DE DATOS Y GRÁFICO ---
    mask = (df['Anio_Limpio'].isin(anios_sel)) & (df['Mes_Limpio'].isin(meses_sel))
    if seleccion_vista != "Mes Total":
        mask = mask & (df['Semana_Filtro'] == seleccion_vista)
    
    df_f = df[mask].copy()
    if emp_sel != "Todas las Empresas":
        df_f = df_f[df_f['Empresa_Limpia'] == emp_sel]

    if not df_f.empty:
        # Se asegura de mostrar meses si se filtra por empresa
        eje_x = 'Mes_Limpio' if emp_sel != "Todas las Empresas" else 'Empresa_Limpia'
        df_plot = df_f.groupby([eje_x, 'Anio_Limpio'])['Usabilidad_Limpia'].mean().reset_index()

        fig_main = go.Figure()
        
        for a in sorted(anios_sel):
            df_a = df_plot[df_plot['Anio_Limpio'] == a]
            if not df_a.empty:
                x_labels = [meses_map.get(m) for m in df_a[eje_x]] if eje_x == 'Mes_Limpio' else df_a[eje_x]
                fig_main.add_trace(go.Bar(
                    x=x_labels, y=df_a['Usabilidad_Limpia'],
                    name=str(a), marker_color=colores.get(a),
                    text=[f"{v:.1%}" for v in df_a['Usabilidad_Limpia']], textposition='outside',
                    textfont=dict(size=14, color="black")
                ))
                # Línea de tendencia (Meta)
                fig_main.add_hline(y=metas[a], line_dash="dot", line_color=colores[a], 
                                  annotation_text=f"Meta {a}", annotation_position="right")
        
        fig_main.update_layout(
            paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)', 
            barmode='group',
            yaxis=dict(tickformat=".0%", gridcolor='rgba(0,0,0,0.1)', tickfont=dict(color="black", size=14)),
            xaxis=dict(tickfont=dict(color="black", size=14)),
            legend=dict(orientation="h", y=1.1, x=0.5, xanchor="center", font=dict(size=16))
        )
        st.plotly_chart(fig_main, use_container_width=True)

        # --- ANÁLISIS DE RANKING ---
        st.markdown("<br>", unsafe_allow_html=True)
        st.markdown("### 📊 Top 5 Empresas con Mayor Usabilidad")
        top_5 = df_f.groupby('Empresa_Limpia')['Usabilidad_Limpia'].mean().nlargest(5).reset_index()
        top_5.columns = ['Empresa', 'Usabilidad Promedio']
        top_5['Usabilidad Promedio'] = top_5['Usabilidad Promedio'].map('{:.2%}'.format)
        st.table(top_5)

except Exception as e:
    st.error(f"Se detectó un detalle técnico: {e}")
