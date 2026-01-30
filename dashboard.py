import streamlit as st
import pandas as pd
import plotly.graph_objects as go

# 1. Configuración de página
st.set_page_config(page_title="Reporte de Usabilidad - Beholos", layout="wide")

# Link que me proporcionaste
URL_DATOS = "https://docs.google.com/spreadsheets/d/e/2PACX-1vSWiXR7BLxwzX2wtD_uF59pvxtus8BL5iqgymKSh2-Llwt6smOJzR7ROUxICr57DA/pub?output=csv"

# --- ESTILO CSS PARA QUE SE VEA PROFESIONAL ---
st.markdown("""
    <style>
        .stApp { background-color: #D1E9F6; } 
        h1 { color: #1E293B; font-family: 'Arial'; font-weight: bold; }
        .stMetric { background-color: white; padding: 15px; border-radius: 10px; box-shadow: 2px 2px 5px rgba(0,0,0,0.1); }
    </style>
""", unsafe_allow_html=True)

@st.cache_data(ttl=300)
def cargar_datos():
    try:
        # Cargamos el CSV desde el link público
        df = pd.read_csv(URL_DATOS)
        # Limpieza de nombres de columnas
        df.columns = [str(c).strip() for c in df.columns]
        
        # Intentar identificar las columnas por palabras clave
        col_empresa = next((c for c in df.columns if 'Empresa' in c or 'Nombre' in c), df.columns[0])
        col_usabilidad = next((c for c in df.columns if 'Usabilidad' in c or 'Engagement' in c), None)
        col_anio = next((c for c in df.columns if 'Año' in c or 'Anio' in c), None)
        col_mes = next((c for c in df.columns if 'Mes' in c), None)

        # Limpiar la columna de usabilidad (quitar % y convertir a número)
        if col_usabilidad:
            df['Usabilidad_Limpia'] = df[col_usabilidad].astype(str).str.replace('%', '').str.replace(',', '.').astype(float)
            # Si el número es mayor a 1, asumimos que es porcentaje entero (ej: 85 en vez de 0.85)
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
    # --- FILTROS EN EL SIDEBAR ---
    with st.sidebar:
        st.header("🎛️ Filtros")
        
        # Filtro de Empresa
        lista_empresas = sorted(df[col_emp].unique().tolist())
        empresa_sel = st.selectbox("Selecciona Empresa", ["Todas"] + lista_empresas)
        
        # Filtro de Año
        if col_ani:
            anios = sorted(df[col_ani].dropna().unique().tolist(), reverse=True)
            anio_sel = st.multiselect("Año", anios, default=anios)
        else:
            anio_sel = []

    # Filtrar el DataFrame
    df_filtrado = df.copy()
    if empresa_sel != "Todas":
        df_filtrado = df_filtrado[df_filtrado[col_emp] == empresa_sel]
    if col_ani and anio_sel:
        df_filtrado = df_filtrado[df_filtrado[col_ani].isin(anio_sel)]

    # --- INDICADORES (GAUGES) ---
    st.subheader(f"Resultado: {empresa_sel}")
    
    promedio = df_filtrado['Usabilidad_Limpia'].mean()
    
    col1, col2 = st.columns([1, 2])
    
    with col1:
        # Gráfico de velocímetro (Gauge)
        fig_gauge = go.Figure(go.Indicator(
            mode = "gauge+number",
            value = promedio * 100,
            number = {'suffix': "%", 'valueformat': '.1f'},
            title = {'text': "Promedio de Usabilidad"},
            gauge = {
                'axis': {'range': [0, 100]},
                'bar': {'color': "#1E293B"},
                'steps': [
                    {'range': [0, 50], 'color': "#FF9F86"},
                    {'range': [50, 80], 'color': "#F1FB8C"},
                    {'range': [80, 100], 'color': "#A9C1F5"}
                ],
            }
        ))
        fig_gauge.update_layout(height=300, margin=dict(l=20, r=20, t=50, b=20), paper_bgcolor='rgba(0,0,0,0)')
        st.plotly_chart(fig_gauge, use_container_width=True)

    with col2:
        # --- GRÁFICO DE TENDENCIA ---
        if col_mes:
            st.write("### Evolución Mensual")
            # Ordenar meses para el gráfico
            df_mes = df_filtrado.groupby(col_mes)['Usabilidad_Limpia'].mean().reset_index()
            
            fig_linea = go.Figure()
            fig_linea.add_trace(go.Scatter(
                x=df_mes[col_mes], 
                y=df_mes['Usabilidad_Limpia'],
                mode='lines+markers',
                line=dict(color='#1E293B', width=3),
                marker=dict(size=10)
            ))
            fig_linea.update_layout(
                yaxis=dict(tickformat=".0%", range=[0, 1]),
                paper_bgcolor='rgba(0,0,0,0)',
                plot_bgcolor='rgba(0,0,0,0)',
                height=300
            )
            st.plotly_chart(fig_linea, use_container_width=True)

    # Tabla de datos al final
    with st.expander("Ver detalles de los datos"):
        st.dataframe(df_filtrado[[col_emp, col_ani, col_mes, 'Usabilidad_Limpia']])

else:
    st.info("Cargando datos desde Google Sheets...")
