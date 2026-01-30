import streamlit as st
import pandas as pd
import plotly.graph_objects as go
import os
from streamlit_gsheets import GSheetsConnection

# 1. Configuración Premium
st.set_page_config(page_title="Holos | Executive Dashboard", layout="wide", initial_sidebar_state="expanded")

# --- PALETA DE COLORES HOLOS ---
AZUL_HOLOS = "#1E293B"
AMARILLO_HOLOS = "#FACC15"
CORAL_HOLOS = "#FB923C"
AZUL_CLARO = "#A9C1F5"

# --- ESTILO CSS AVANZADO ---
st.markdown(f"""
    <link href="https://fonts.googleapis.com/css2?family=Philosopher:wght@400;700&family=Inter:wght@300;400;600&display=swap" rel="stylesheet">
    <style>
        * {{ font-family: 'Inter', sans-serif; }}
        h1 {{ font-family: 'Philosopher', sans-serif !important; color: {AZUL_HOLOS}; font-size: 2.8rem !important; margin-bottom: 0px; }}
        h3 {{ font-family: 'Philosopher', sans-serif !important; color: {AZUL_HOLOS}; margin-top: 20px; }}
        .stApp {{ background-color: #F8FAFC; }} 
        [data-testid="stSidebar"] {{ background-color: #FFFFFF; border-right: 1px solid #E2E8F0; }}
        .stMetric {{ background-color: white; padding: 15px; border-radius: 10px; box-shadow: 0 2px 4px rgba(0,0,0,0.05); }}
    </style>
""", unsafe_allow_html=True)

def encontrar_columna(df, palabras_clave):
    for col in df.columns:
        for palabra in palabras_clave:
            if palabra.lower() in col.lower(): return col
    return None

@st.cache_data(ttl=300)
def load_data():
    conn = st.connection("gsheets", type=GSheetsConnection)
    # Leemos ambas pestañas usando los nombres exactos o índices
    try:
        df1 = conn.read(worksheet="2024-2025")
        df2 = conn.read(worksheet="2026")
        df = pd.concat([df1, df2], ignore_index=True)
    except:
        df = conn.read() # Fallback si las pestañas cambian de nombre

    df.columns = [str(c).strip() for c in df.columns]
    c_emp = encontrar_columna(df, ['Nombre', 'Empresa'])
    c_usa = encontrar_columna(df, ['% Usabilidad', 'Engagement', 'Usabilidad'])
    c_mes = encontrar_columna(df, ['Inicio del Mes', 'Mes'])
    c_ani = encontrar_columna(df, ['Inicio de Año', 'Año'])
    c_sem = encontrar_columna(df, ['Semana', 'Desglose']) 

    def limpiar_pct(row):
        valor = row[c_usa]
        s = str(valor).replace('%', '').replace(',', '.').strip()
        try:
            n = float(s)
            return n / 100.0 if n > 1.1 else n
        except: return 0.0

    df['Usabilidad_Limpia'] = df.apply(limpiar_pct, axis=1)
    df['Anio_Limpio'] = pd.to_numeric(df[c_ani], errors='coerce').fillna(0).astype(int)
    df['Mes_Limpio'] = pd.to_numeric(df[c_mes], errors='coerce').fillna(0).astype(int)
    df['Empresa_Limpia'] = df[c_emp].astype(str).str.strip()
    df['Semana_Filtro'] = df[c_sem].astype(str).str.strip() if c_sem else "Mes Total"
    return df, c_emp

try:
    df, real_col_emp = load_data()
    
    # --- HEADER ---
    col_t, col_l = st.columns([4, 1])
    with col_t:
        st.markdown("<h1>Business Intelligence Report</h1>", unsafe_allow_html=True)
        st.caption("Consolidado Estratégico de Usabilidad 2024 - 2026")
    with col_l:
        # Aquí puedes poner tu logo o un placeholder
        st.markdown(f"**HOLOS**")

    # --- SIDEBAR ---
    with st.sidebar:
        st.markdown("### 🎛️ Filtros de Análisis")
        empresas_unicas = sorted([e for e in df['Empresa_Limpia'].unique() if e not in ['nan', 'None']])
        emp_sel = st.selectbox("Empresa Target", ["Todas las Empresas"] + empresas_unicas)
        
        anios_disp = sorted(df['Anio_Limpio'].unique(), reverse=True)
        anios_sel = st.multiselect("Comparativa Anual", anios_disp, default=anios_disp)
        
        meses_map = {1:'Ene', 2:'Feb', 3:'Mar', 4:'Abr', 5:'May', 6:'Jun', 7:'Jul', 8:'Ago', 9:'Set', 10:'Oct', 11:'Nov', 12:'Dic'}
        meses_sel = st.multiselect("Rango de Meses", sorted(meses_map.keys()), default=sorted(meses_map.keys()), format_func=lambda x: meses_map[x])

        seleccion_vista = st.selectbox("Detalle Temporal", ["Mes Total"] + [opt for opt in df['Semana_Filtro'].unique() if "total" not in opt.lower()])

    # --- FILTRADO ---
    mask = (df['Anio_Limpio'].isin(anios_sel)) & (df['Mes_Limpio'].isin(meses_sel))
    if seleccion_vista != "Mes Total":
        mask = mask & (df['Semana_Filtro'] == seleccion_vista)
    
    df_f = df[mask].copy()
    if emp_sel != "Todas las Empresas":
        df_f = df_f[df_f['Empresa_Limpia'] == emp_sel]

    # --- GAUGES ---
    colores_dict = {2024: CORAL_HOLOS, 2025: AMARILLO_HOLOS, 2026: AZUL_HOLOS}
    
    if anios_sel:
        st.markdown("### 🎯 Kpis de Rendimiento Anual")
        gauge_cols = st.columns(len(anios_sel))
        for idx, anio in enumerate(sorted(anios_sel)):
            with gauge_cols[idx]:
                val = df_f[df_f['Anio_Limpio'] == anio]['Usabilidad_Limpia'].mean()
                fig_g = go.Figure(go.Indicator(
                    mode="gauge+number", value=(val or 0)*100,
                    number={'suffix': "%", 'font': {'size': 24, 'color': AZUL_HOLOS}, 'valueformat':'.1f'},
                    title={'text': f"Ciclo {anio}", 'font': {'size': 14}},
                    gauge={'axis': {'range': [0, 100]}, 
                           'bar': {'color': AZUL_HOLOS},
                           'bgcolor': "white",
                           'steps': [{'range': [0, 100], 'color': colores_dict.get(anio, "#F1F5F9")}]}
                ))
                fig_g.update_layout(height=180, margin=dict(l=20, r=20, t=30, b=10), paper_bgcolor='rgba(0,0,0,0)')
                st.plotly_chart(fig_g, use_container_width=True, key=f"g_{anio}")

    # --- TENDENCIA ---
    st.markdown("### 📈 Evolución Estratégica")
    df_plot = df_f.groupby(['Mes_Limpio', 'Anio_Limpio'])['Usabilidad_Limpia'].mean().reset_index()
    fig_main = go.Figure()
    for a in sorted(anios_sel):
        df_a = df_plot[df_plot['Anio_Limpio'] == a].sort_values('Mes_Limpio')
        if not df_a.empty:
            fig_main.add_trace(go.Scatter(
                x=[meses_map.get(m) for m in df_a['Mes_Limpio']], y=df_a['Usabilidad_Limpia'],
                name=f"Año {a}", mode='lines+markers+text',
                line=dict(color=colores_dict.get(a), width=4),
                text=[f"{v:.1%}" for v in df_a['Usabilidad_Limpia']], textposition="top center"
            ))
    fig_main.update_layout(
        hovermode="x unified", height=400,
        yaxis=dict(tickformat=".0%", gridcolor='#E2E8F0'),
        legend=dict(orientation="h", y=1.1, x=0.5, xanchor="center")
    )
    st.plotly_chart(fig_main, use_container_width=True)

    # --- INFORME INTELIGENTE ---
    st.markdown("### 🧠 Executive Insights")
    c1, c2, c3 = st.columns(3)
    avg_total = df_f['Usabilidad_Limpia'].mean()
    
    with c1:
        st.metric("Engagement Promedio", f"{avg_total:.1%}", delta=f"{(avg_total-0.7):.1%}")
    with c2:
        top_month = df_f.groupby('Mes_Limpio')['Usabilidad_Limpia'].mean().idxmax()
        st.metric("Mes de Oro", meses_map[top_month])
    with c3:
        status = "Saludable" if avg_total > 0.75 else "Atención"
        st.metric("Estado de Cuenta", status)

    # --- RANKING (SOLO SI ES TODAS) ---
    if emp_sel == "Todas las Empresas":
        st.markdown("### 🏆 Ranking de Empresas (Top Performance)")
        top_df = df_f.groupby('Empresa_Limpia')['Usabilidad_Limpia'].mean().nlargest(10).reset_index()
        st.dataframe(top_df.style.format({ 'Usabilidad_Limpia': '{:.1%}' }).background_gradient(cmap='YlGnBu'), use_container_width=True)

except Exception as e:
    st.error(f"Error de Integración: {e}")
