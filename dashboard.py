import streamlit as st
import pandas as pd
import plotly.graph_objects as go
from streamlit_gsheets import GSheetsConnection

# 1. Configuración de página
st.set_page_config(page_title="Reporte de Usabilidad", layout="wide")

# --- ESTILO CSS ---
st.markdown("""
    <link href="https://fonts.googleapis.com/css2?family=Philosopher:wght@400;700&family=Inter:wght@300;400;600&display=swap" rel="stylesheet">
    <style>
        * { font-family: 'Inter', sans-serif; }
        h1 { font-family: 'Philosopher', sans-serif !important; color: #1E293B; font-size: 2.8rem !important; }
        .stApp { background-color: #D1E9F6; } 
    </style>
""", unsafe_allow_html=True)

@st.cache_data(ttl=300)
def cargar_todo():
    conn = st.connection("gsheets", type=GSheetsConnection)
    try:
        # Leer Pestaña 1 (2024-2025) y Pestaña 2 (2026)
        df1 = conn.read(worksheet=0)
        df2 = conn.read(worksheet=1)
        df = pd.concat([df1, df2], ignore_index=True)
        
        df.columns = [str(c).strip() for c in df.columns]
        
        # Identificar columnas
        c_emp = next((c for c in df.columns if 'Empresa' in c or 'Nombre' in c), df.columns[0])
        c_usa = next((c for c in df.columns if 'Usabilidad' in c or 'Engagement' in c), df.columns[1])
        c_mes = next((c for c in df.columns if 'Mes' in c), df.columns[2])
        c_ani = next((c for c in df.columns if 'Año' in c or 'Anio' in c), df.columns[3])

        # Limpiar datos
        df['Val_Usa'] = pd.to_numeric(df[c_usa].astype(str).str.replace('%', '').str.replace(',', '.'), errors='coerce').fillna(0)
        if df['Val_Usa'].max() > 1.1: df['Val_Usa'] = df['Val_Usa'] / 100
        
        df['Anio_Limpio'] = pd.to_numeric(df[c_ani], errors='coerce').fillna(0).astype(int)
        df['Mes_Limpio'] = pd.to_numeric(df[c_mes], errors='coerce').fillna(0).astype(int)
        df['Empresa_Limpia'] = df[c_emp].astype(str).str.strip()
        
        return df, 'Empresa_Limpia', 'Anio_Limpio', 'Mes_Limpio'
    except Exception as e:
        st.error(f"Error al conectar: {e}")
        return pd.DataFrame(), None, None, None

df, col_emp, col_ani, col_mes = cargar_todo()

if not df.empty:
    # --- SIDEBAR ---
    with st.sidebar:
        st.markdown("### 🎛️ Filtros")
        empresas_unicas = sorted([e for e in df[col_emp].unique() if e not in ['nan', 'None', '']])
        # AQUI AGREGAMOS "Todas las Empresas"
        emp_sel = st.selectbox("Empresa Target", ["Todas las Empresas"] + empresas_unicas)
        
        anios_disp = sorted([a for a in df[col_ani].unique() if a > 2000], reverse=True)
        anios_sel = st.multiselect("Comparativa Anual", anios_disp, default=anios_disp)
        
        meses_map = {1:'Ene', 2:'Feb', 3:'Mar', 4:'Abr', 5:'May', 6:'Jun', 7:'Jul', 8:'Ago', 9:'Set', 10:'Oct', 11:'Nov', 12:'Dic'}
        meses_sel = st.multiselect("Meses", sorted(meses_map.keys()), default=sorted(meses_map.keys()), format_func=lambda x: meses_map[x])

    st.markdown(f"<h1>📊 Reporte de Usabilidad: {emp_sel}</h1>", unsafe_allow_html=True)

    # Lógica de filtrado con opción "Todas"
    df_f = df[df[col_ani].isin(anios_sel) & df[col_mes].isin(meses_sel)].copy()
    if emp_sel != "Todas las Empresas":
        df_f = df_f[df_f[col_emp] == emp_sel]

    # --- GAUGES POR AÑO ---
    colores = {2024: "#F1FB8C", 2025: "#FF9F86", 2026: "#A9C1F5"}
    
    if anios_sel:
        cols = st.columns(len(anios_sel))
        for i, a in enumerate(sorted(anios_sel)):
            with cols[i]:
                val = df_f[df_f[col_ani] == a]['Val_Usa'].mean()
                if pd.isna(val): val = 0
                fig = go.Figure(go.Indicator(
                    mode="gauge+number", value=val*100,
                    number={'suffix': "%", 'font': {'size': 24}},
                    title={'text': f"Promedio {a}", 'font': {'size': 16}},
                    gauge={'axis': {'range': [0, 100]}, 'bar': {'color': colores.get(a, "#CBD5E1")}}
                ))
                fig.update_layout(height=180, margin=dict(l=20, r=20, t=40, b=10), paper_bgcolor='rgba(0,0,0,0)')
                st.plotly_chart(fig, use_container_width=True, key=f"g_{a}")

    # --- GRÁFICO DE EVOLUCIÓN ---
    st.markdown("### 📈 Evolución Estratégica")
    df_plot = df_f.groupby([col_mes, col_ani])['Val_Usa'].mean().reset_index()
    
    fig_main = go.Figure()
    for a in sorted(anios_sel):
        df_a = df_plot[df_plot[col_ani] == a].sort_values(col_mes)
        if not df_a.empty:
            fig_main.add_trace(go.Scatter(
                x=[meses_map[m] for m in df_a[col_mes]], 
                y=df_a['Val_Usa'],
                name=f"Año {a}", mode='lines+markers+text',
                text=[f"{v:.1%}" for v in df_a['Val_Usa']],
                textposition="top center",
                line=dict(color=colores.get(a), width=4)
            ))
    
    fig_main.update_layout(
        yaxis=dict(tickformat=".0%", range=[0, 1.1]),
        paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)',
        legend=dict(orientation="h", y=1.1, x=0.5, xanchor="center")
    )
    st.plotly_chart(fig_main, use_container_width=True)

    with st.expander("Ver tabla de datos consolidada"):
        st.dataframe(df_f)
