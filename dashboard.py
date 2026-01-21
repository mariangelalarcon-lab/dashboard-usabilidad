import streamlit as st
import pandas as pd
import plotly.graph_objects as go
import os

# 1. Configuración de página de alta definición
st.set_page_config(page_title="Holos Executive Dashboard", layout="wide", initial_sidebar_state="expanded")

# --- ESTILO CSS AVANZADO ---
st.markdown("""
    <link href="https://fonts.googleapis.com/css2?family=Philosopher:wght@400;700&family=Inter:wght@300;400;600&display=swap" rel="stylesheet">
    <style>
        /* Estética General */
        * { font-family: 'Inter', sans-serif; }
        h1, h2, h3 { font-family: 'Philosopher', sans-serif !important; color: #1E293B; }
        .stApp { background-color: #F8FAFC; } /* Gris ultra claro para contraste */
        
        /* Sidebar Profesional */
        [data-testid="stSidebar"] { background-color: #FFFFFF; border-right: 1px solid #E2E8F0; }
        .stSelectbox label { font-weight: 600; color: #475569; }
        
        /* Contenedores de KPIs */
        .metric-card {
            background-color: white; padding: 20px; border-radius: 12px;
            box-shadow: 0 4px 6px -1px rgba(0,0,0,0.1); border: 1px solid #E2E8F0;
        }
        
        /* Ajuste de Gráficos */
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
        st.warning("No se encontraron archivos de datos (CSV).")
        st.stop()

    # --- SIDEBAR (FILTROS PRO) ---
    with st.sidebar:
        st.image("image_e57c24.png", width=120) if os.path.exists("image_e57c24.png") else None
        st.markdown("### 🎛️ Panel de Control")
        
        empresas_unicas = sorted([e for e in df['Empresa_Limpia'].unique() if e != 'nan'])
        emp_sel = st.selectbox("Empresa Target", ["Todas las Empresas"] + empresas_unicas)
        
        # Filtro de año único o comparación simple para no saturar
        anios_disponibles = sorted(df['Anio_Limpio'].unique(), reverse=True)
        anios_sel = st.multiselect("Comparativa Anual", anios_disponibles, default=anios_disponibles[:2])
        
        meses_map = {1:'Ene', 2:'Feb', 3:'Mar', 4:'Abr', 5:'May', 6:'Jun', 7:'Jul', 8:'Ago', 9:'Set', 10:'Oct', 11:'Nov', 12:'Dic'}
        meses_sel = st.multiselect("Rango de Meses", sorted(meses_map.keys()), default=sorted(meses_map.keys()), format_func=lambda x: meses_map[x])

        st.markdown("---")
        opciones_raw = sorted(df['Semana_Filtro'].unique().tolist())
        opciones_vistas = ["Mes Total"] + [opt for opt in opciones_raw if "total" not in opt.lower()]
        seleccion_vista = st.selectbox("Detalle Temporal", opciones_vistas)

    # --- ENCABEZADO ---
    header_col, logo_col = st.columns([4, 1])
    with header_col:
        st.markdown(f"<h1>Executive Report: {emp_sel}</h1>", unsafe_allow_html=True)
        st.markdown(f"<p style='color: #64748b; font-size: 1.1rem;'>Análisis estratégico de usabilidad y engagement.</p>", unsafe_allow_html=True)
    with logo_col:
        if os.path.exists("image_e57c24.png"):
            st.image("image_e57c24.png", width=140)

    # --- INDICADORES CLAVE (GAUGES) ---
    colores_dict = {2024: "#F1FB8C", 2025: "#FF9F86", 2026: "#A9C1F5"}
    metas = {2024: 0.35, 2025: 0.40, 2026: 0.45}
    
    gauge_cols = st.columns(len(anios_sel)) if anios_sel else [st.container()]
    for idx, anio in enumerate(sorted(anios_sel)):
        with gauge_cols[idx]:
            data_anio = df[(df['Anio_Limpio'] == anio)]
            if emp_sel != "Todas las Empresas":
                data_anio = data_anio[data_anio['Empresa_Limpia'] == emp_sel]
            
            avg_val = data_anio['Usabilidad_Limpia'].mean()
            
            fig_g = go.Figure(go.Indicator(
                mode="gauge+number", value=avg_val*100,
                number={'suffix': "%", 'font': {'size': 32, 'color': '#1E293B'}, 'valueformat':'.1f'},
                title={'text': f"Promedio {anio}", 'font': {'size': 18, 'color': '#64748B'}},
                gauge={'axis': {'range': [0, 100]}, 'bar': {'color': colores_dict.get(anio, "#CBD5E1")},
                       'bgcolor': "white", 'bordercolor': "#E2E8F0"}
            ))
            fig_g.update_layout(height=200, margin=dict(l=10, r=10, t=40, b=10), paper_bgcolor='rgba(0,0,0,0)')
            st.plotly_chart(fig_g, use_container_width=True, key=f"g_{anio}")

    # --- LÓGICA DE DATOS PARA EL GRÁFICO PRINCIPAL ---
    mask = (df['Anio_Limpio'].isin(anios_sel)) & (df['Mes_Limpio'].isin(meses_sel))
    if seleccion_vista != "Mes Total":
        mask = mask & (df['Semana_Filtro'] == seleccion_vista)
    
    df_f = df[mask].copy()
    if emp_sel != "Todas las Empresas":
        df_f = df_f[df_f['Empresa_Limpia'] == emp_sel]

    # --- GRÁFICO DE TENDENCIA MENSUAL ---
    st.markdown("### 📈 Evolución Estratégica")
    if not df_f.empty:
        # Siempre agrupamos por mes para ver la tendencia temporal
        df_plot = df_f.groupby(['Mes_Limpio', 'Anio_Limpio'])['Usabilidad_Limpia'].mean().reset_index()
        
        fig_main = go.Figure()
        for a in sorted(anios_sel):
            df_a = df_plot[df_plot['Anio_Limpio'] == a].sort_values('Mes_Limpio')
            if not df_a.empty:
                x_names = [meses_map.get(m) for m in df_a['Mes_Limpio']]
                fig_main.add_trace(go.Scatter(
                    x=x_names, y=df_a['Usabilidad_Limpia'],
                    name=f"Año {a}", mode='lines+markers+text',
                    line=dict(color=colores_dict.get(a), width=4),
                    marker=dict(size=10),
                    text=[f"{v:.1%}" for v in df_a['Usabilidad_Limpia']],
                    textposition="top center"
                ))
        
        fig_main.update_layout(
            hovermode="x unified",
            paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)',
            yaxis=dict(tickformat=".0%", gridcolor='#E2E8F0', range=[0, max(df_plot['Usabilidad_Limpia'])*1.2]),
            xaxis=dict(showgrid=False),
            legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1)
        )
        st.plotly_chart(fig_main, use_container_width=True)

    # --- SECCIÓN DE ANÁLISIS INTELIGENTE (INSIGHTS) ---
    st.markdown("### 🧠 Insights del Analista AI")
    col_ins1, col_ins2 = st.columns(2)
    
    with col_ins1:
        if not df_f.empty:
            mejor_mes_idx = df_f.groupby('Mes_Limpio')['Usabilidad_Limpia'].mean().idxmax()
            mejor_val = df_f.groupby('Mes_Limpio')['Usabilidad_Limpia'].mean().max()
            st.info(f"🚀 **Pico de Usabilidad:** El rendimiento más alto se registró en **{meses_map[mejor_mes_idx]}** con un **{mejor_val:.1%}**.")
            
            # Cálculo de semestre
            primer_sem = df_f[df_f['Mes_Limpio'] <= 6]['Usabilidad_Limpia'].mean()
            segundo_sem = df_f[df_f['Mes_Limpio'] > 6]['Usabilidad_Limpia'].mean()
            if not pd.isna(segundo_sem):
                tendencia = "crecimiento" if segundo_sem > primer_sem else "contracción"
                st.write(f"📊 El segundo semestre muestra una tendencia de **{tendencia}** comparado con el primero.")

    with col_ins2:
        if len(anios_sel) >= 2:
            a_reciente = max(anios_sel)
            a_previo = min(anios_sel)
            val_reciente = df[df['Anio_Limpio'] == a_reciente]['Usabilidad_Limpia'].mean()
            val_previo = df[df['Anio_Limpio'] == a_previo]['Usabilidad_Limpia'].mean()
            diff = (val_reciente - val_previo) / (val_previo if val_previo != 0 else 1)
            st.success(f"📈 **Crecimiento Interanual:** La usabilidad ha variado un **{diff:+.1%}$ en comparación al año anterior.")

    # --- RANKING DE EMPRESAS ---
    if emp_sel == "Todas las Empresas":
        st.markdown("### 🏆 Ranking de Performance (Top 5)")
        top_5 = df_f.groupby('Empresa_Limpia')['Usabilidad_Limpia'].mean().nlargest(5).reset_index()
        top_5.columns = ['Empresa', 'Usabilidad Media']
        
        # Tabla estilizada
        st.dataframe(top_5.style.format({'Usabilidad Media': '{:.2%}'})
                     .background_gradient(cmap='Blues', subset=['Usabilidad Media']), 
                     use_container_width=True)

except Exception as e:
    st.error(f"Error en Dashboard: {e}")
