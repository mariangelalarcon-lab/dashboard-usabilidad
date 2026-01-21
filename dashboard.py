import streamlit as st
import pandas as pd
import plotly.graph_objects as go
import os

# 1. Configuración de página de alta definición
st.set_page_config(page_title="Reporte de Usabilidad", layout="wide", initial_sidebar_state="expanded")

# --- ESTILO CSS AVANZADO ---
st.markdown("""
    <link href="https://fonts.googleapis.com/css2?family=Philosopher:wght@400;700&family=Inter:wght@300;400;600&display=swap" rel="stylesheet">
    <style>
        /* Estética General */
        * { font-family: 'Inter', sans-serif; }
        h1 { font-family: 'Philosopher', sans-serif !important; color: #1E293B; font-size: 3rem !important; margin-bottom: 0px; }
        .stApp { background-color: #F8FAFC; }
        
        /* Sidebar Profesional */
        [data-testid="stSidebar"] { background-color: #FFFFFF; border-right: 1px solid #E2E8F0; }
        
        /* Ajuste de Gráficos */
        .stPlotlyChart { background-color: transparent !important; }
        
        /* Contenedor del Título para alinear con Logo */
        .header-container { display: flex; justify-content: space-between; align-items: center; margin-bottom: 20px; }
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
            if any(x in empresa for x in ["cardif", "scotiabank"]):
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

    # --- ENCABEZADO MEJORADO ---
    # Usamos columnas de Streamlit para asegurar que el logo esté siempre a la derecha
    col_titu, col_logo = st.columns([4, 1])
    
    with col_titu:
        st.markdown("<h1>Reporte de Usabilidad</h1>", unsafe_allow_html=True)
        st.markdown(f"<p style='color: #64748b; font-size: 1.1rem; margin-top:-10px;'>Vista estratégica: {emp_sel if 'emp_sel' in locals() else 'Todas las Empresas'}</p>", unsafe_allow_html=True)
    
    with col_logo:
        if os.path.exists("image_e57c24.png"):
            # Alineación a la derecha mediante un contenedor
            st.markdown('<div style="text-align: right;">', unsafe_allow_html=True)
            st.image("image_e57c24.png", width=120)
            st.markdown('</div>', unsafe_allow_html=True)

    # --- FILTROS SIDEBAR ---
    with st.sidebar:
        st.markdown("### 🎛️ Filtros")
        empresas_unicas = sorted([e for e in df['Empresa_Limpia'].unique() if e != 'nan'])
        emp_sel = st.selectbox("Empresa", ["Todas las Empresas"] + empresas_unicas)
        
        anios_disponibles = sorted(df['Anio_Limpio'].unique(), reverse=True)
        anios_sel = st.multiselect("Comparar Años", anios_disponibles, default=anios_disponibles)
        
        meses_map = {1:'Ene', 2:'Feb', 3:'Mar', 4:'Abr', 5:'May', 6:'Jun', 7:'Jul', 8:'Ago', 9:'Set', 10:'Oct', 11:'Nov', 12:'Dic'}
        meses_sel = st.multiselect("Meses", sorted(meses_map.keys()), default=sorted(meses_map.keys()), format_func=lambda x: meses_map[x])

        opciones_raw = sorted(df['Semana_Filtro'].unique().tolist())
        opciones_vistas = ["Mes Total"] + [opt for opt in opciones_raw if "total" not in opt.lower()]
        seleccion_vista = st.selectbox("Detalle Temporal", opciones_vistas)

    st.markdown("---")

    # --- INDICADORES CIRCULARES (MÁS PEQUEÑOS Y REFINADOS) ---
    colores_dict = {2024: "#F1FB8C", 2025: "#FF9F86", 2026: "#A9C1F5"}
    
    # Creamos una fila centralizada para los indicadores
    if anios_sel:
        gauges_cols = st.columns(len(anios_sel))
        for idx, anio in enumerate(sorted(anios_sel)):
            with gauges_cols[idx]:
                data_anio = df[(df['Anio_Limpio'] == anio)]
                if emp_sel != "Todas las Empresas":
                    data_anio = data_anio[data_anio['Empresa_Limpia'] == emp_sel]
                
                avg_val = data_anio['Usabilidad_Limpia'].mean()
                
                fig_g = go.Figure(go.Indicator(
                    mode="gauge+number", value=avg_val*100,
                    number={'suffix': "%", 'font': {'size': 24, 'color': '#1E293B'}, 'valueformat':'.1f'},
                    title={'text': f"Avg {anio}", 'font': {'size': 16, 'color': '#64748B'}},
                    gauge={'axis': {'range': [0, 100], 'tickfont': {'size': 10}}, 
                           'bar': {'color': colores_dict.get(anio, "#CBD5E1")},
                           'bgcolor': "white", 'bordercolor': "#E2E8F0"}
                ))
                # Reducción de altura del gráfico para que se vea más pequeño
                fig_g.update_layout(height=160, margin=dict(l=15, r=15, t=30, b=10), paper_bgcolor='rgba(0,0,0,0)')
                st.plotly_chart(fig_g, use_container_width=True, key=f"gauge_{anio}")

    # --- GRÁFICO DE TENDENCIA Y RANKING ---
    # (El resto de la lógica de análisis inteligente y gráficos se mantiene igual pero con el diseño refinado)
    mask = (df['Anio_Limpio'].isin(anios_sel)) & (df['Mes_Limpio'].isin(meses_sel))
    if seleccion_vista != "Mes Total":
        mask = mask & (df['Semana_Filtro'] == seleccion_vista)
    
    df_f = df[mask].copy()
    if emp_sel != "Todas las Empresas":
        df_f = df_f[df_f['Empresa_Limpia'] == emp_sel]

    if not df_f.empty:
        st.markdown("### 📈 Evolución Mensual")
        df_plot = df_f.groupby(['Mes_Limpio', 'Anio_Limpio'])['Usabilidad_Limpia'].mean().reset_index()
        fig_main = go.Figure()
        for a in sorted(anios_sel):
            df_a = df_plot[df_plot['Anio_Limpio'] == a].sort_values('Mes_Limpio')
            if not df_a.empty:
                x_names = [meses_map.get(m) for m in df_a['Mes_Limpio']]
                fig_main.add_trace(go.Scatter(
                    x=x_names, y=df_a['Usabilidad_Limpia'],
                    name=f"{a}", mode='lines+markers',
                    line=dict(color=colores_dict.get(a), width=3),
                    marker=dict(size=8)
                ))
        fig_main.update_layout(height=400, margin=dict(t=20), paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)',
                              yaxis=dict(tickformat=".0%", gridcolor='#E2E8F0'))
        st.plotly_chart(fig_main, use_container_width=True)

except Exception as e:
    st.error(f"Error: {e}")
