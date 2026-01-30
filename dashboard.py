import streamlit as st
import pandas as pd
import plotly.graph_objects as go

# 1. Configuración de página
st.set_page_config(page_title="Reporte de Usabilidad - Beholos", layout="wide")

# Link público
URL_DATOS = "https://docs.google.com/spreadsheets/d/e/2PACX-1vSWiXR7BLxwzX2wtD_uF59pvxtus8BL5iqgymKSh2-Llwt6smOJzR7ROUxICr57DA/pub?output=csv"

# --- ESTILO CSS ---
st.markdown("""
    <style>
        .stApp { background-color: #D1E9F6; } 
        h1 { color: #1E293B; font-family: 'Arial'; font-weight: bold; }
        [data-testid="stMetricValue"] { color: #1E293B; }
    </style>
""", unsafe_allow_html=True)

@st.cache_data(ttl=300)
def cargar_datos():
    try:
        df = pd.read_csv(URL_DATOS)
        df.columns = [str(c).strip() for c in df.columns]
        
        # Identificar columnas automáticamente
        col_empresa = next((c for c in df.columns if 'Empresa' in c or 'Nombre' in c), df.columns[0])
        col_usabilidad = next((c for c in df.columns if 'Usabilidad' in c or 'Engagement' in c), None)
        col_anio = next((c for c in df.columns if 'Año' in c or 'Anio' in c), None)
        col_mes = next((c for c in df.columns if 'Mes' in c), None)

        # Limpiar datos: Convertir a string y quitar nulos en empresas
        df[col_empresa] = df[col_empresa].astype(str).replace('nan', 'Desconocido')
        
        # Limpiar Usabilidad
        if col_usabilidad:
            df['Usabilidad_Limpia'] = pd.to_numeric(df[col_usabilidad].astype(str).str.replace('%', '').str.replace(',', '.'), errors='coerce').fillna(0)
            if df['Usabilidad_Limpia'].max() > 1:
                df['Usabilidad_Limpia'] = df['Usabilidad_Limpia'] / 100
        
        return df, col_empresa, col_anio, col_mes
    except Exception as e:
        st.error(f"Error al procesar los datos: {e}")
        return pd.DataFrame(), None, None, None

# --- LÓGICA DEL DASHBOARD ---
st.title("📊 Reporte de Usabilidad")

df, col_emp, col_ani, col_mes = cargar_datos()

if not df.empty:
    with st.sidebar:
        st.header("🎛️ Filtros")
        
        # EL CAMBIO AQUÍ: Filtramos nulos antes de ordenar
        opciones_empresa = [e for e in df[col_emp].unique() if e and e != 'Desconocido']
        empresa_sel = st.selectbox("Selecciona Empresa", ["Todas"] + sorted(opciones_empresa))
        
        if col_ani:
            anios = [a for a in df[col_ani].unique() if pd.notna(a)]
            anio_sel = st.multiselect("Año", sorted(anios, reverse=True), default=sorted(anios, reverse=True))

    # Filtrar
    df_filtrado = df.copy()
    if empresa_sel != "Todas":
        df_filtrado = df_filtrado[df_filtrado[col_emp] == empresa_sel]
    if col_ani and anio_sel:
        df_filtrado = df_filtrado[df_filtrado[col_ani].isin(anio_sel)]

    # --- VISUALIZACIÓN ---
    st.subheader(f"Análisis: {empresa_sel}")
    
    promedio = df_filtrado['Usabilidad_Limpia'].mean()
    
    c1, c2 = st.columns([1, 2])
    
    with c1:
        fig_gauge = go.Figure(go.Indicator(
            mode = "gauge+number",
            value = promedio * 100,
            number = {'suffix': "%", 'valueformat': '.1f', 'font': {'size': 40}},
            gauge = {
                'axis': {'range': [0, 100]},
                'bar': {'color': "#1E293B"},
                'steps': [
                    {'range': [0, 50], 'color': "#FF9F86"},
                    {'range': [50, 85], 'color': "#F1FB8C"},
                    {'range': [85, 100], 'color': "#A9C1F5"}
                ],
            }
        ))
        fig_gauge.update_layout(height=300, margin=dict(l=30, r=30, t=30, b=30), paper_bgcolor='rgba(0,0,0,0)')
        st.plotly_chart(fig_gauge, use_container_width=True)

    with c2:
        if col_mes:
            # Agrupar por mes para la tendencia
            df_mes = df_filtrado.groupby(col_mes)['Usabilidad_Limpia'].mean().reset_index()
            fig_line = go.Figure(go.Scatter(
                x=df_mes[col_mes], y=df_mes['Usabilidad_Limpia'],
                mode='lines+markers+text',
                text=[f"{v:.1%}" for v in df_mes['Usabilidad_Limpia']],
                textposition="top center",
                line=dict(color='#1E293B', width=4)
            ))
            fig_line.update_layout(
                yaxis=dict(tickformat=".0%", range=[0, 1.1]),
                height=300, margin=dict(l=10, r=10, t=10, b=10),
                paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)'
            )
            st.plotly_chart(fig_line, use_container_width=True)

    with st.expander("Ver tabla de datos detallada"):
        st.dataframe(df_filtrado)

else:
    st.error("No se detectaron datos. Revisa el link de Google Sheets.")
