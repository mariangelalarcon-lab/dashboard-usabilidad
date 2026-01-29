import streamlit as st
import pandas as pd
from streamlit_gsheets import GSheetsConnection

st.set_page_config(page_title="Diagnóstico de Conexión", layout="wide")

st.title("🔍 Diagnóstico Maestro de Conexión")

# Definimos el link directamente aquí para evitar errores de Secrets
URL_SHEET = "https://docs.google.com/spreadsheets/d/1bnhhWjkBJKEoie7_PuKRUSjAebnkst7d/edit"

try:
    # Intentamos conectar usando el link directo
    conn = st.connection("gsheets", type=GSheetsConnection)
    
    # Intentamos leer la primera pestaña disponible usando el link directo
    df = conn.read(spreadsheet=URL_SHEET)
    
    if df is not None:
        st.success("✅ ¡CONEXIÓN EXITOSA!")
        st.write("### Columnas detectadas:")
        st.write(list(df.columns))
        st.write("### Vista previa de datos:")
        st.dataframe(df.head())
    else:
        st.error("El archivo devolvió un objeto vacío.")

except Exception as e:
    st.error(f"❌ Error crítico de conexión: {e}")
    
    st.markdown("""
    ### Si sigues viendo Error 404, revisa esto:
    1. **En GitHub:** Revisa tu archivo `requirements.txt`. Debe tener exactamente estas líneas:
       ```
       streamlit
       pandas
       st-gsheets-connection
       ```
    2. **En Streamlit Cloud:** Borra la App y vuelve a crearla desde el repositorio. A veces la "instancia" de la App se queda corrupta con el error 404 y no se limpia con un reinicio.
    """)
