import streamlit as st
import pandas as pd
import plotly.graph_objects as go

# 1. Configuración de página
st.set_page_config(page_title="Reporte de Usabilidad", layout="wide")

# Link que proporcionaste
URL_DATOS = "https://docs.google.com/spreadsheets/d/e/2PACX-1vSWiXR7BLxwzX2wtD_uF59pvxtus8BL5iqgymKSh2-Llwt6smOJzR7ROUxICr57DA/pub?output=csv"

# --- ESTILO CSS PERSONALIZADO (Mismo que el original) ---
st.markdown("""
    <link href="https://fonts.googleapis.com/css2?family=Philosopher:wght@400;700&family=Inter:wght@300;400;600&display=swap" rel="stylesheet">
    <style>
        * { font-family: 'Inter', sans-serif; }
        h1 { font-family: 'Philosopher', sans-serif !important; color: #1E293B; font-size: 2.8rem !important; }
        .stApp { background-color: #D1E9F6; } 
        [data-testid="stSidebar"] { background-color: #FFFFFF; }
    </style>
""", unsafe_allow_html=True)

@st.cache_data(ttl=300)
def cargar_y_limpiar():
    try:
        df = pd.read_csv(URL_DATOS)
        df.columns = [str(c).strip() for c in df.columns]
        
        # Mapeo de columnas según tu captura
        c_emp = 'Nombre de la Empresa'
        c_usa = 'Engagement %' if 'Engagement %' in df.columns else df.columns[df.columns.str.contains('Usabilidad|Engagement', case=False)][0]
        c_mes = 'Mes' if 'Mes' in df.columns else df.columns[df.columns.str.contains('Mes', case=False)][0]
        c_ani = 'Año' if 'Año' in df.columns else df.columns[df.columns.str.contains('Año|Anio', case=False)][0]
        c_sem = 'Semana'

        # Limpieza de Usabilidad
        df['Val_Usa'] = pd.to_numeric(df[c_usa].astype(str).str.replace('%', '').str.replace(',', '.'), errors='coerce').fillna(0)
        # Si los valores vienen como 80.0 en vez de 0.8, dividimos por 100
        if df['Val_Usa'].max() > 1.1:
            df['Val_Usa'] = df['Val_Usa'] / 100

        # Limpieza de Años y Meses
        df['Anio_Limpio'] = pd.to_numeric(df[c_ani], errors='coerce').fillna(0).astype(int)
        df['Mes_Limpio'] = pd.to_numeric(df[c_mes], errors='coerce').fillna(0).astype(int)
        df['Empresa_Limpia'] = df[c_emp].astype(str).str.strip()
        
        return df, 'Empresa_Limpia', 'Anio_Limpio', 'Mes_Limpio', c_sem
    except Exception as e:
        st.error(f"Error procesando datos: {e}")
        return pd.DataFrame(), None, None, None, None

df, col_emp, col_ani, col_mes, col_sem = cargar_y_limpiar()

if not df.empty:
    # --- SIDEBAR ---
    with st.sidebar:
        st.markdown("### 🎛️ Filtros")
        empresas_unicas = sorted([e for e in df[col_emp].unique() if e != 'nan'])
        emp_sel = st.selectbox("Empresa Target", empresas_unicas)
        
        anios_disp = sorted(df[col_ani].unique(), reverse=True)
        anios_sel = st.multiselect("Comparativa Anual", anios_disp, default=[2024, 2025])
        
        meses_map = {1:'Ene', 2:'Feb', 3:'Mar', 4:'Abr', 5:'May', 6:'Jun', 7:'Jul', 8:'Ago', 9:'Set', 10:'Oct', 11:'Nov', 12:'Dic'}
        meses_sel = st.multiselect("Meses", sorted(meses_map.keys()), default=sorted(meses_map.keys()), format_func=lambda x: meses_map[x])

    st.markdown(f"<h1>📊 Reporte de Usabilidad: {emp_sel}</h1>", unsafe_allow_html=True)

    # Filtrado
    df_f = df[(df[col_emp] == emp_sel) & (df[col_ani].isin(anios_sel)) & (df[col_mes].isin(meses_sel))].copy()

    # --- GAUGES POR AÑO (Como el original) ---
    colores = {2024: "#F1FB8C", 2025: "#FF9F86", 2023: "#A9C1F5", 2026: "#A9C1F5"}
    
    if anios_sel:
        cols = st.columns(len(anios_sel))
        for i, a in enumerate(sorted(anios_sel)):
            with cols[i]:
                val = df_f[df_f[col_ani] == a]['Val_Usa'].mean()
                fig = go.Figure(go.Indicator(
                    mode="gauge+number", value=val*100,
                    number={'suffix': "%", 'font': {'size': 24}},
                    title={'text': f"Promedio {a}", 'font': {'size': 16}},
                    gauge={'axis': {'range': [0, 100]}, 'bar': {'color': colores.get(a, "#CBD5E1")}}
                ))
                fig.update_layout(height=180, margin=dict(l=20, r=20, t=40, b=10), paper_bgcolor='rgba(0,0,0,0)')
                st.plotly_chart(fig, use_container_width=True)

    # --- GRÁFICO DE EVOLUCIÓN ---
    st.markdown("### 📈 Evolución Estratégica")
    df_plot = df_f.groupby([col_mes, col_ani])['Val_Usa'].mean().reset_index()
    
    fig_main = go.Figure()
    for a in sorted(anios_sel):
        df_a = df_plot[df_plot[col_ani] == a].sort_values(col_mes)
        fig_main.add_trace(go.Scatter(
            x=[meses_map[m] for m in df_a[col_mes]], 
            y=df_a['Val_Usa'],
            name=f"Año {a}", mode='lines+markers',
            line=dict(color=colores.get(a), width=4)
        ))
    
    fig_main.update_layout(
        yaxis=dict(tickformat=".0%", range=[0, 1]),
        paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)',
        legend=dict(orientation="h", y=1.1)
    )
    st.plotly_chart(fig_main, use_container_width=True)

    with st.expander("Ver tabla de datos detallada"):
        st.dataframe(df_f)
