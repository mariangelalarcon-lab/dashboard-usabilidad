import streamlit as st
import pandas as pd
import plotly.graph_objects as go

# 1. Configuración de pantalla
st.set_page_config(page_title="Holos | BI Dashboard", layout="wide")

# --- ENLACES ---
LINK_1 = "https://docs.google.com/spreadsheets/d/e/2PACX-1vSWiXR7BLxwzX2wtD_uF59pvxtus8BL5iqgymKSh2-Llwt6smOJzR7ROUxICr57DA/pub?gid=1638907402&single=true&output=csv"
LINK_2 = "https://docs.google.com/spreadsheets/d/e/2PACX-1vSWiXR7BLxwzX2wtD_uF59pvxtus8BL5iqgymKSh2-Llwt6smOJzR7ROUxICr57DA/pub?gid=1341962834&single=true&output=csv"

# Colores Holos
SKY, LEAF, SEA, CORAL, BLACK, WHITE = "#D1E9F6", "#F1FB8C", "#A9C1F5", "#FF9F86", "#000000", "#FFFFFF"

@st.cache_data(ttl=5)
def cargar_data_captura():
    try:
        df1 = pd.read_csv(LINK_1)
        df2 = pd.read_csv(LINK_2)
        df = pd.concat([df1, df2], ignore_index=True)
        # Limpiar nombres de columnas (quitar espacios locos)
        df.columns = [str(c).strip() for c in df.columns]

        # MAPEo BASADO EN TU CAPTURA DE EXCEL:
        # Columna A: Nombre de la Empresa
        # Columna B: Semana
        # Columna H: % Usabilidad/Engagement
        # Columna J: Inicio del Mes  <-- ESTA ES LA CLAVE
        # Columna L: Inicio del Año  <-- ESTA ES LA OTRA CLAVE

        c_emp = "Nombre de la Empresa"
        c_sem = "Semana"
        c_usa = "% Usabilidad/Engagement"
        c_mes = "Inicio del Mes"
        c_ani = "Inicio del Año"

        # Validar que las columnas existan, si no, buscarlas por aproximación
        cols = df.columns.tolist()
        c_mes = next((c for c in cols if "Inicio del Mes" in c), cols[9]) # J es la 10ma
        c_ani = next((c for c in cols if "Inicio del Año" in c), cols[11]) # L es la 12va

        # Limpieza de datos
        df['Anio_V'] = pd.to_numeric(df[c_ani], errors='coerce').fillna(0).astype(int)
        df['Mes_V'] = pd.to_numeric(df[c_mes], errors='coerce').fillna(0).astype(int)
        df['Empresa_V'] = df[c_emp].astype(str).str.strip()
        df['Semana_V'] = df[c_sem].astype(str).str.strip()
        
        def limpiar_pct(val):
            try:
                s = str(val).replace('%', '').replace(',', '.').strip()
                n = float(s)
                return n / 100.0 if n > 1.1 else n
            except: return 0.0
        df['Usabilidad_V'] = df[c_usa].apply(limpiar_pct)

        return df
    except Exception as e:
        st.error(f"Error cargando columnas: {e}")
        return pd.DataFrame()

df = cargar_data_captura()

# --- INTERFAZ ---
st.markdown(f"<style>.stApp {{ background-color: {SKY}; }}</style>", unsafe_allow_html=True)

if not df.empty:
    with st.sidebar:
        st.header("🎛️ Filtros")
        modo = st.radio("Ver datos como:", ["Resumen Mensual (Cierres)", "Detalle Semanal (Avance)"], index=1)
        
        # Filtro de Año y Mes (Pre-seleccionamos 2026 y Feb según tu captura)
        anios_sel = st.multiselect("Años", sorted(df['Anio_V'].unique(), reverse=True), default=[2026])
        meses_sel = st.multiselect("Meses", [1,2,3,4,5,6,7,8,9,10,11,12], default=[1, 2],
                                   format_func=lambda x: ['','Ene','Feb','Mar','Abr','May','Jun','Jul','Ago','Set','Oct','Nov','Dic'][x])
        
        empresa_sel = st.selectbox("Seleccionar Empresa", ["Todas las Empresas"] + sorted(df['Empresa_V'].unique()))

    # --- FILTRADO ---
    df_f = df[(df['Anio_V'].isin(anios_sel)) & (df['Mes_V'].isin(meses_sel))]
    if empresa_sel != "Todas las Empresas":
        df_f = df_f[df_f['Empresa_V'] == empresa_sel]

    # Diferenciar Cierres de Semanas
    if "Cierres" in modo:
        df_vis = df_f[df_f['Semana_V'].str.contains('total|Total', case=False, na=False)]
    else:
        # Excluimos los totales para ver solo el progreso de las semanas 1, 2, 3...
        df_vis = df_f[~df_f['Semana_V'].str.contains('total|Total', case=False, na=False)]

    st.title(f"📊 Reporte: {empresa_sel}")

    if not df_vis.empty:
        # Gráfica de evolución
        df_chart = df_vis.groupby(['Anio_V', 'Mes_V', 'Semana_V'])['Usabilidad_V'].mean().reset_index()
        df_chart = df_chart.sort_values(['Anio_V', 'Mes_V', 'Semana_V'])
        
        fig = go.Figure()
        meses_map = {1:'Ene', 2:'Feb', 3:'Mar', 4:'Abr', 5:'May', 6:'Jun', 7:'Jul', 8:'Ago', 9:'Set', 10:'Oct', 11:'Nov', 12:'Dic'}
        
        for a in sorted(df_chart['Anio_V'].unique()):
            d = df_chart[df_chart['Anio_V'] == a]
            # Eje X combinado como me pediste
            x_labels = [f"{meses_map.get(m)}-{s}" for m, s in zip(d['Mes_V'], d['Semana_V'])]
            
            fig.add_trace(go.Scatter(
                x=x_labels, y=d['Usabilidad_V'], name=f"Año {a}",
                mode='lines+markers+text', text=[f"{v:.1%}" for v in d['Usabilidad_V']],
                textposition="top center", line=dict(width=3)
            ))
        
        fig.update_layout(yaxis=dict(tickformat=".0%", range=[0, 1.1]), height=450, paper_bgcolor='rgba(0,0,0,0)')
        st.plotly_chart(fig, use_container_width=True)
        
        # TABLA DE VERIFICACIÓN
        st.markdown("### 📝 Detalle de registros encontrados")
        st.dataframe(df_vis[['Empresa_V', 'Anio_V', 'Mes_V', 'Semana_V', 'Usabilidad_V']].sort_values(['Anio_V', 'Mes_V', 'Semana_V'], ascending=False))
    else:
        st.warning("No hay datos para los filtros seleccionados. Verifica que 'Año' sea 2026 y 'Mes' sea 2 en el Sidebar.")

else:
    st.error("Error crítico: No se pudo leer el archivo. Revisa los permisos de publicación del Google Sheets.")
