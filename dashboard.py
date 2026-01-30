import streamlit as st
import pandas as pd
import plotly.graph_objects as go

# 1. Configuración de página
st.set_page_config(page_title="Reporte de Usabilidad", layout="wide")

# --- PEGA TUS LINKS AQUÍ ---
LINK_24_25 = "https://docs.google.com/spreadsheets/d/e/2PACX-1vSWiXR7BLxwzX2wtD_uF59pvxtus8BL5iqgymKSh2-Llwt6smOJzR7ROUxICr57DA/pub?gid=1341962834&single=true&output=csv"
LINK_2026 = "https://docs.google.com/spreadsheets/d/e/2PACX-1vSWiXR7BLxwzX2wtD_uF59pvxtus8BL5iqgymKSh2-Llwt6smOJzR7ROUxICr57DA/pub?gid=1638907402&single=true&output=csv"

# --- ESTILO CSS ---
st.markdown("""
    <style>
        .stApp { background-color: #D1E9F6; } 
        h1 { color: #1E293B; font-family: 'Arial'; font-weight: bold; }
    </style>
""", unsafe_allow_html=True)

@st.cache_data(ttl=300)
def cargar_consolidado():
    try:
        # Leemos ambas pestañas directamente
        df1 = pd.read_csv(LINK_24_25)
        df2 = pd.read_csv(LINK_2026)
        
        # Unimos los datos
        df = pd.concat([df1, df2], ignore_index=True)
        df.columns = [str(c).strip() for c in df.columns]
        
        # Nombres de columnas según tu Excel
        c_emp = 'Nombre de la Empresa'
        c_usa = 'Engagement %'
        c_mes = 'Mes'
        c_ani = 'Año'

        # Limpieza de datos
        df['Val_Usa'] = pd.to_numeric(df[c_usa].astype(str).str.replace('%', '').str.replace(',', '.'), errors='coerce').fillna(0)
        if df['Val_Usa'].max() > 1.1: df['Val_Usa'] = df['Val_Usa'] / 100
        
        df['Anio_Limpio'] = pd.to_numeric(df[c_ani], errors='coerce').fillna(0).astype(int)
        df['Mes_Limpio'] = pd.to_numeric(df[c_mes], errors='coerce').fillna(0).astype(int)
        df['Empresa_Limpia'] = df[c_emp].astype(str).str.strip()
        
        return df, 'Empresa_Limpia', 'Anio_Limpio', 'Mes_Limpio'
    except Exception as e:
        st.error(f"Error al leer los datos: {e}")
        return pd.DataFrame(), None, None, None

df, col_emp, col_ani, col_mes = cargar_consolidado()

if not df.empty:
    with st.sidebar:
        st.header("🎛️ Filtros")
        # Filtro con opción "Todas"
        empresas = sorted([e for e in df[col_emp].unique() if e not in ['nan', 'None', '', 'nan']])
        emp_sel = st.selectbox("Selecciona Empresa", ["Todas las Empresas"] + empresas)
        
        anios_disp = sorted([a for a in df[col_ani].unique() if a > 2000], reverse=True)
        anios_sel = st.multiselect("Años", anios_disp, default=anios_disp)

    st.title(f"📊 Reporte: {emp_sel}")

    # Filtrado lógico
    df_f = df[df[col_ani].isin(anios_sel)].copy()
    if emp_sel != "Todas las Empresas":
        df_f = df_f[df_f[col_emp] == emp_sel]

    # --- GAUGES ---
    colores = {2024: "#F1FB8C", 2025: "#FF9F86", 2026: "#A9C1F5"}
    
    # Mostrar solo los años que tengan datos tras filtrar la empresa
    anios_con_datos = sorted(df_f[col_ani].unique())
    if anios_con_datos:
        cols = st.columns(len(anios_con_datos))
        for i, a in enumerate(anios_con_datos):
            with cols[i]:
                val = df_f[df_f[col_ani] == a]['Val_Usa'].mean()
                fig = go.Figure(go.Indicator(
                    mode="gauge+number", value=val*100,
                    number={'suffix': "%", 'font': {'size': 24}},
                    title={'text': f"Promedio {a}", 'font': {'size': 18}},
                    gauge={'axis': {'range': [0, 100]}, 'bar': {'color': colores.get(a, "#1E293B")}}
                ))
                fig.update_layout(height=200, margin=dict(l=20, r=20, t=40, b=10), paper_bgcolor='rgba(0,0,0,0)')
                st.plotly_chart(fig, use_container_width=True, key=f"gauge_{a}")

    # --- TABLA ---
    with st.expander("Ver datos consolidados (2024-2026)"):
        st.dataframe(df_f[[col_emp, col_ani, col_mes, 'Val_Usa']])
else:
    st.warning("Cargando datos... Asegúrate de haber pegado ambos links de 'Publicar en la web'.")
