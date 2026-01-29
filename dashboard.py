import streamlit as st
import pandas as pd
from streamlit_gsheets import GSheetsConnection

st.title("🔍 Diagnóstico de Datos")

try:
    conn = st.connection("gsheets", type=GSheetsConnection)
    
    # Intentamos leer la primera pestaña disponible
    df = conn.read()
    
    if df is not None:
        st.success("✅ ¡Conexión exitosa! Se detectaron datos.")
        
        st.subheader("Nombres de las columnas detectadas:")
        st.write(list(df.columns))
        
        st.subheader("Vista previa de las primeras 5 filas:")
        st.dataframe(df.head())
        
        st.subheader("Información de las pestañas:")
        st.info("Si lo que ves arriba no es tu tabla de usabilidad, es que hay filas vacías al inicio o la pestaña correcta no es la primera.")
    else:
        st.error("El archivo está vacío o no se puede leer.")

except Exception as e:
    st.error(f"Error de conexión: {e}")
