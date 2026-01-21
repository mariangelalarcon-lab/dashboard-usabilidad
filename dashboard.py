import streamlit as st
import pandas as pd
import plotly.graph_objects as go
import os

# 1. Configuración de página
st.set_page_config(page_title="Reporte de Usabilidad Holos", layout="wide")

# Estilo: Fondo celeste, fuentes y transparencia
st.markdown("""
    <link href="https://fonts.googleapis.com/css2?family=Philosopher:wght@400;700&display=swap" rel="stylesheet">
    <style>
        * { font-family: 'Philosopher', sans-serif !important; }
        .stApp { background-color: #D1E9F6; }
        .stSelectbox, .stMultiSelect { background-color: white; border-radius: 8px; }
        h1 { color: #000000; font-weight: 700; font-size: 2.8rem !important; margin: 0; }
        [data-testid="stSidebar"] { background-color: #FFFFFF; }
        /* Eliminar bordes y fondos de contenedores de gráficos */
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
            # Casos especiales Cardif/Scotiabank
            if "cardif" in empresa or "scotiabank" in empresa:
                return n / 10000.0 if n > 1.0 else n / 100.0
            return n / 100.0 if n > 1.0 else n
        except: return 0.0

    df['Usabilidad_Limpia'] = df.apply(limpiar_pct, axis=1)
    df['Anio_Limpio'] = pd.to_numeric(df[c_ani], errors='coerce').fillna(0).astype(int)
    df = df[df['Anio_Limpio'] > 2020].copy()
    df['Mes_Limpio'] = pd.to_numeric(df[c_mes], errors='coerce').fillna(0).astype(int)
    df['Empresa_Limpia'] = df[c_emp].astype(str).str.strip()
    
    if c_sem:
        df['Semana_Filtro'] = df[c_sem].astype(str).str.strip()
    else:
        df['Semana_Filtro'] = "Mes total"
    return df

try:
    df = load_data()
    if df.empty:
        st.warning("No se encontraron archivos CSV.")
        st.stop()

    # --- ENCABEZADO ---
    col_logo, col_tit, col_g1, col_g2, col_g3 = st.columns([0.6, 1.4, 1, 1, 1])
    
    with col_logo:
        # Busca el logo con el nombre que tienes en tu carpeta
        logo_path = "image_e57c24.png" if os.path.exists("image_e57c24.png") else "logo.png"
        if os.path.exists(logo_path):
            st.image(logo_path, width=120)

    with col_tit:
        st.markdown("<h1>Reporte de Usabilidad</h1>", unsafe_allow_html=True)

    # --- SIDEBAR ---
    with st.sidebar:
        st.markdown("### ⚙️ Configuración")
        empresas_unicas = sorted([e for e in df['Empresa_Limpia'].unique() if e != 'nan'])
        emp_sel = st.selectbox("Empresa", ["Todas las Empresas"] + empresas_unicas)
        anios_sel = st.multiselect("Año", sorted(df['Anio_Limpio'].unique()), default=sorted(df['Anio_Limpio'].unique()))
        
        meses_map = {1:'Ene', 2:'Feb', 3:'Mar', 4:'Abr', 5:'May', 6:'Jun', 7:'Jul', 8:'Ago', 9:'Set', 10:'Oct', 11:'Nov', 12:'Dic'}
        meses_sel = st.multiselect("Mes", sorted(meses_map.keys()), default=[1], format_func=lambda x: meses_map[x])

        st.markdown("---")
        opciones_raw = sorted(df['Semana_Filtro'].unique().tolist())
        opciones_sin_total = [opt for opt in opciones_raw if "total" not in opt.lower()]
        opciones_menu = ["Acumulado"] + opciones_sin_total
        seleccion_vista = st.selectbox("Vista Temporal", opciones_menu)

    # --- INDICADORES CIRCULARES (GAUGES) ---
    def crear_gauge(anio, color, key):
        # Para el gauge superior, siempre calculamos el promedio total del año para dar el acumulado real
        data_a = df[df['Anio_Limpio'] == anio]
        if emp_sel != "Todas las Empresas":
            data_a = data_a[data_a['Empresa_Limpia'] == emp_sel]
            
        val = data_a['Usabilidad_Limpia'].mean()
        if pd.isna(val) or val == 0: return
        
        fig = go.Figure(go.Indicator(
            mode="gauge+number", value=val*100,
            number={'suffix': "%", 'font': {'size': 20, 'color': '#000000'}, 'valueformat':'.2f'},
            title={'text': f"Avg {anio}", 'font': {'size': 15, 'color': '#000000'}},
            gauge={'axis': {'range': [0, 100], 'tickcolor': "black"}, 
                   'bar': {'color': color},
                   'bgcolor': "rgba(255,255,255,0.5)",
                   'bordercolor': "black"}
        ))
        fig.update_layout(height=160, margin=dict(l=20, r=20, t=40, b=10), paper_bgcolor='rgba(0,0,0,0)')
        st.plotly_chart(fig, use_container_width=True, key=key)

    with col_g1:
        if 2024 in anios_sel: crear_gauge(2024, "#A9C1F5", "c24")
    with col_g2:
        if 2025 in anios_sel: crear_gauge(2025, "#FF9F86", "c25")
    with col_g3:
        if 2026 in anios_sel: crear_gauge(2026, "#F1FB8C", "c26")

    # --- LÓGICA DE FILTRADO PARA EL GRÁFICO ---
    mask = (df['Anio_Limpio'].isin(anios_sel)) & (df['Mes_Limpio'].isin(meses_sel))
    
    if seleccion_vista != "Acumulado":
        mask = mask & (df['Semana_Filtro'] == seleccion_vista)
    
    df_f = df[mask].copy()
    if emp_sel != "Todas las Empresas":
        df_f = df_f[df_f['Empresa_Limpia'] == emp_sel]

    # --- GRÁFICO PRINCIPAL TRANSPARENTE ---
    if not df_f.empty:
        # Si es acumulado, agrupamos para sacar el promedio real de lo que hay
        eje_x = 'Empresa_Limpia' if emp_sel == "Todas las Empresas" else 'Mes_Limpio'
        df_plot = df_f.groupby([eje_x, 'Anio_Limpio'])['Usabilidad_Limpia'].mean().reset_index()

        fig_main = go.Figure()
        colores = {2024: "#A9C1F5", 2025: "#FF9F86", 2026: "#F1FB8C"}
        
        for a in sorted(anios_sel):
            df_a = df_plot[df_plot['Anio_Limpio'] == a]
            if not df_a.empty:
                x_labels = df_a[eje_x] if emp_sel == "Todas las Empresas" else [meses_map.get(m) for m in df_a['Mes_Limpio']]
                fig_main.add_trace(go.Bar(
                    x=x_labels, y=df_a['Usabilidad_Limpia'],
                    name=f"Año {a}", marker_color=colores.get(a),
                    text=[f"{v:.2%}" for v in df_a['Usabilidad_Limpia']], textposition='outside'
                ))
        
        fig_main.update_layout(
            paper_bgcolor='rgba(0,0,0,0)', 
            plot_bgcolor='rgba(0,0,0,0)', 
            barmode='group',
            yaxis=dict(tickformat=".1%", title="Usabilidad", gridcolor='rgba(0,0,0,0.1)', tickfont=dict(color="black")),
            xaxis=dict(tickfont=dict(color="black")),
            legend=dict(orientation="h", y=1.2, x=0.5, xanchor="center")
        )
        st.plotly_chart(fig_main, use_container_width=True)

        # --- ANÁLISIS RANKING (TOP 5) ---
        st.markdown("---")
        st.subheader("🏆 Ranking: Top 5 Empresas con Mayor Usabilidad")
        top_5 = df_f.groupby('Empresa_Limpia')['Usabilidad_Limpia'].mean().nlargest(5).reset_index()
        top_5.columns = ['Empresa', 'Promedio Usabilidad']
        top_5['Promedio Usabilidad'] = top_5['Promedio Usabilidad'].map('{:.2%}'.format)
        st.table(top_5)

    else:
        st.info("No hay datos suficientes para los filtros seleccionados.")

except Exception as e:
    st.error(f"Error técnico detectado: {e}")
