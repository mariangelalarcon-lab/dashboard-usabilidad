import streamlit as st
import pandas as pd
import plotly.graph_objects as go

st.set_page_config(page_title="Reporte de Usabilidad", layout="wide")

# PEGA AQUÍ EL LINK QUE COPIASTE EN EL PASO ANTERIOR
# Debe terminar en output=csv
URL_CSV = "TU_LINK_DE_PUBLICAR_EN_LA_WEB_AQUI"

@st.cache_data(ttl=600)
def load_data():
    try:
        # Leemos directamente el CSV público
        df = pd.read_csv(URL_CSV)
        return df
    except Exception as e:
        st.error(f"Error al leer el CSV: {e}")
        return pd.DataFrame()

st.title("📊 Reporte de Usabilidad (Modo Directo)")

df = load_data()

if not df.empty:
    st.success("¡Datos cargados con éxito!")
    st.write("### Vista previa de los datos encontrados:")
    st.dataframe(df.head())
    
    # Aquí ya podríamos re-insertar toda tu lógica de gráficos
else:
    st.warning("Aún no podemos acceder a los datos. Asegúrate de haberle dado a 'Publicar' en el Excel.")
