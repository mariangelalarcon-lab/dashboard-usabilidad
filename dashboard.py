import streamlit as st
import pandas as pd
import plotly.graph_objects as go
from streamlit_gsheets import GSheetsConnection

st.set_page_config(page_title="Reporte de Usabilidad", layout="wide")

# --- ESTILO CSS ---
st.markdown("""
    <style>
        .stApp { background-color: #D1E9F6; } 
        h1 { color: #1E293B; font-family: 'Arial'; font-weight: bold; }
    </style>
""", unsafe_allow_html=True)

@st.cache_data(ttl=300)
def cargar_consolidado():
    conn = st.connection("gsheets", type=GSheetsConnection)
    try:
        # Intentamos leer por nombre de pestaña. 
        # SI TUS PESTAÑAS TIENEN OTROS NOMBRES, CÁMBIALOS AQUÍ:
        df1 = conn.read(worksheet="2024-2025") 
        df2 = conn.read(worksheet="2026")
        
        df = pd.concat([df1, df2], ignore_index=True)
        df.columns = [str(c).strip() for c in df.columns]
        
        # Mapeo de columnas
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
        st.error(f"Error al leer las pestañas: {e}. Revisa los nombres de las hojas en el Excel.")
        return pd.DataFrame(), None, None, None

df, col_emp, col_ani, col_mes = cargar_consolidado()

if not df.empty:
    with st.sidebar:
        st.header("🎛️ Filtros")
        empresas = sorted([e for e in df[col_emp].unique() if e not in ['nan', 'None', '']])
        emp_sel = st.selectbox("Selecciona Empresa", ["Todas las Empresas"] + empresas)
        
        anios_disp = sorted([a for a in df[col_ani].unique() if a > 2000], reverse=True)
        anios_sel = st.multiselect("Años", anios_disp, default=anios_disp)

    st.title(f"📊 Reporte: {emp_sel}")

    # Filtrado
    df_f = df[df[col_ani].isin(anios_sel)].copy()
    if emp_sel != "Todas las Empresas":
        df_f = df_f[df_f[col_emp] == emp_sel]

    # --- GAUGES ---
    colores = {2024: "#F1FB8C", 2025: "#FF9F86", 2026: "#A9C1F5"}
    cols = st.columns(len(anios_sel))
    for i, a in enumerate(sorted(anios_sel)):
        with cols[i]:
            val = df_f[df_f[col_ani] == a]['Val_Usa'].mean()
            if pd.isna(val): val = 0
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
    st.warning("No se pudo cargar la información. Verifica que el archivo requirements.txt incluya st-gsheets-connection.")
