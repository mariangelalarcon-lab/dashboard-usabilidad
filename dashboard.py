import streamlit as st
import pandas as pd
import plotly.graph_objects as go

# 1. Configuración de página
st.set_page_config(page_title="Reporte de Usabilidad - Beholos", layout="wide")

# --- ENLACES REALES QUE ME PROPORCIONASTE ---
LINK_1 = "https://docs.google.com/spreadsheets/d/e/2PACX-1vSWiXR7BLxwzX2wtD_uF59pvxtus8BL5iqgymKSh2-Llwt6smOJzR7ROUxICr57DA/pub?gid=1638907402&single=true&output=csv"
LINK_2 = "https://docs.google.com/spreadsheets/d/e/2PACX-1vSWiXR7BLxwzX2wtD_uF59pvxtus8BL5iqgymKSh2-Llwt6smOJzR7ROUxICr57DA/pub?gid=1341962834&single=true&output=csv"

# --- ESTILO CSS ---
st.markdown("""
    <style>
        .stApp { background-color: #D1E9F6; } 
        h1 { color: #1E293B; font-family: 'Arial'; font-weight: bold; }
    </style>
""", unsafe_allow_html=True)

@st.cache_data(ttl=300)
def cargar_datos_consolidados():
    try:
        # Cargamos ambas fuentes
        df1 = pd.read_csv(LINK_1)
        df2 = pd.read_csv(LINK_2)
        
        # Unimos las tablas (esto junta 2024, 2025 y 2026)
        df = pd.concat([df1, df2], ignore_index=True)
        
        # Limpieza de nombres de columnas (quita espacios invisibles)
        df.columns = [str(c).strip() for c in df.columns]
        
        # Buscamos las columnas por palabras clave para evitar errores
        c_emp = next((c for c in df.columns if 'Empresa' in c or 'Nombre' in c), df.columns[0])
        c_usa = next((c for c in df.columns if 'Engagement' in c or 'Usabilidad' in c), None)
        c_ani = next((c for c in df.columns if 'Año' in c or 'Anio' in c), None)
        c_mes = next((c for c in df.columns if 'Mes' in c), None)

        # Si no encuentra la columna de valor, lanzamos aviso
        if not c_usa:
            st.error("No se detectó la columna de Engagement/Usabilidad.")
            return pd.DataFrame(), None, None, None

        # Limpiar el valor de Usabilidad/Engagement
        df['Val_Usa'] = pd.to_numeric(df[c_usa].astype(str).str.replace('%', '').str.replace(',', '.'), errors='coerce').fillna(0)
        # Si el número es mayor a 1, es un porcentaje entero (ej: 85 -> 0.85)
        if df['Val_Usa'].max() > 1.1:
            df['Val_Usa'] = df['Val_Usa'] / 100
        
        # Limpiar Año y Empresa
        df['Anio_Limpio'] = pd.to_numeric(df[c_ani], errors='coerce').fillna(0).astype(int)
        df['Empresa_Limpia'] = df[c_emp].astype(str).str.strip()
        
        return df, 'Empresa_Limpia', 'Anio_Limpio', c_mes
    except Exception as e:
        st.error(f"Error cargando los datos: {e}")
        return pd.DataFrame(), None, None, None

# --- EJECUCIÓN ---
df, col_emp, col_ani, col_mes = cargar_datos_consolidados()

if not df.empty:
    with st.sidebar:
        st.header("🎛️ Filtros")
        # Filtro de empresa con opción "Todas"
        lista_empresas = sorted([e for e in df[col_emp].unique() if e not in ['nan', 'None', '']])
        empresa_sel = st.selectbox("Selecciona Empresa", ["Todas las Empresas"] + lista_empresas)
        
        # Filtro de años
        anios_disponibles = sorted([a for a in df[col_ani].unique() if a > 2000], reverse=True)
        anios_sel = st.multiselect("Años a mostrar", anios_disponibles, default=anios_disponibles)

    st.title(f"📊 Reporte de Usabilidad: {empresa_sel}")

    # Aplicar Filtros
    df_filtrado = df[df[col_ani].isin(anios_sel)].copy()
    if empresa_sel != "Todas las Empresas":
        df_filtrado = df_filtrado[df_filtrado[col_emp] == empresa_sel]

    # --- INDICADORES (GAUGES) ---
    colores_anios = {2024: "#F1FB8C", 2025: "#FF9F86", 2026: "#A9C1F5"}
    
    # Crear columnas para los velocímetros
    if not df_filtrado.empty:
        anios_finales = sorted(df_filtrado[col_ani].unique())
        cols = st.columns(len(anios_finales))
        
        for i, anio in enumerate(anios_finales):
            with cols[i]:
                valor_promedio = df_filtrado[df_filtrado[col_ani] == anio]['Val_Usa'].mean()
                fig = go.Figure(go.Indicator(
                    mode="gauge+number",
                    value=valor_promedio * 100,
                    number={'suffix': "%", 'font': {'size': 26}},
                    title={'text': f"Promedio {anio}", 'font': {'size': 18}},
                    gauge={
                        'axis': {'range': [0, 100]},
                        'bar': {'color': "#1E293B"},
                        'steps': [
                            {'range': [0, 50], 'color': "#E5E7EB"},
                            {'range': [50, 100], 'color': colores_anios.get(anio, "#CBD5E1")}
                        ]
                    }
                ))
                fig.update_layout(height=220, margin=dict(l=20, r=20, t=50, b=20), paper_bgcolor='rgba(0,0,0,0)')
                st.plotly_chart(fig, use_container_width=True, key=f"gauge_{anio}")

    # --- TABLA DE DATOS ---
    with st.expander("📂 Ver registros detallados"):
        st.dataframe(df_filtrado)

else:
    st.warning("No se encontraron datos en los enlaces proporcionados.")
