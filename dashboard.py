import streamlit as st
import pandas as pd
import plotly.graph_objects as go

st.set_page_config(page_title="Reporte Beholos", layout="wide")

# --- COPIA TU LINK AQUÍ ---
# El link que obtuviste en el paso anterior (el de Publicar en la Web)
URL_DATOS = "https://docs.google.com/spreadsheets/d/e/TU_CODIGO_AQUI/pub?output=csv"

@st.cache_data(ttl=300)
def cargar_datos():
    try:
        # Cargamos los datos directamente
        df = pd.read_csv(URL_DATOS)
        # Limpiamos nombres de columnas por si tienen espacios
        df.columns = [str(c).strip() for c in df.columns]
        return df
    except Exception as e:
        st.error(f"No se pudieron cargar los datos: {e}")
        return pd.DataFrame()

st.title("📊 Dashboard de Usabilidad")

df = cargar_datos()

if not df.empty:
    st.success("✅ ¡Conexión exitosa! Datos cargados.")
    
    # Esto te mostrará tus datos en una tabla para confirmar que todo está bien
    st.subheader("Vista previa de la información")
    st.dataframe(df)
    
    # Aquí puedes agregar un gráfico rápido para probar
    st.subheader("Análisis Rápido")
    st.info("Una vez que confirmes que ves la tabla arriba, podemos personalizar tus gráficos.")
else:
    st.warning("Esperando datos... Revisa que hayas publicado el Excel correctamente.")
