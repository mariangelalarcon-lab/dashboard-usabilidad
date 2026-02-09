import streamlit as st
import pandas as pd
import plotly.graph_objects as go

# 1. Configuración de pantalla
st.set_page_config(page_title="Holos | BI Dashboard", layout="wide")

# --- ENLACES ---
LINK_1 = "https://docs.google.com/spreadsheets/d/e/2PACX-1vSWiXR7BLxwzX2wtD_uF59pvxtus8BL5iqgymKSh2-Llwt6smOJzR7ROUxICr57DA/pub?gid=1638907402&single=true&output=csv"
LINK_2 = "https://docs.google.com/spreadsheets/d/e/2PACX-1vSWiXR7BLxwzX2wtD_uF59pvxtus8BL5iqgymKSh2-Llwt6smOJzR7ROUxICr57DA/pub?gid=1341962834&single=true&output=csv"

# Colores Holos
SKY, SEA, CORAL, BLACK = "#D1E9F6", "#A9C1F5", "#FF9F86", "#000000"

@st.cache_data(ttl=5)
def cargar_data_reunion():
    try:
        # Leemos los datos ignorando filas vacías al final
        df1 = pd.read_csv(LINK_1).dropna(how='all')
        df2 = pd.read_csv(LINK_2).dropna(how='all')
        df = pd.concat([df1, df2], ignore_index=True)
        df.columns = [str(c).strip() for c in df.columns]

        # MAPEo DINÁMICO (Basado en tu captura de celdas A, B, H, J, L)
        c_emp = next((c for c in df.columns if "Nombre" in c), df.columns[0])
        c_sem = next((c for c in df.columns if "Semana" in c), df.columns[1])
        c_usa = next((c for c in df.columns if "%" in c or "Usabilidad" in c), df.columns[7])
        c_mes = next((c for c in df.columns if "Inicio del Mes" in c), df.columns[9])
        c_ani = next((c for c in df.columns if "Inicio del Año" in c), df.columns[11])

        # Convertir a tipos de datos puros
        df['Anio_V'] = pd.to_numeric(df[c_ani], errors='coerce').fillna(0).astype(int)
        df['Mes_V'] = pd.to_numeric(df[c_mes], errors='coerce').fillna(0).astype(int)
        df['Empresa_V'] = df[c_emp].astype(str).str.strip()
        df['Semana_V'] = df[c_sem].astype(str).str.strip()
        
        def pct_a_float(val):
            try:
                if pd.isna(val) or val == "": return 0.0
                s = str(val).replace('%', '').replace(',', '.').strip()
                n = float(s)
                return n / 100.0 if n > 1.1 else n
            except: return 0.0
            
        df['Usabilidad_V'] = df[c_usa].apply(pct_a_float)
        
        # Filtro de seguridad: eliminar filas donde la usabilidad sea 0 y no haya empresa
        return df[(df['Anio_V'] > 0) & (df['Empresa_V'] != 'nan')]
    except Exception as e:
        st.error(f"Error de lectura: {e}")
        return pd.DataFrame()

df = cargar_data_reunion()

# UI
st.markdown(f"<style>.stApp {{ background-color: {SKY}; }}</style>", unsafe_allow_html=True)

if not df.empty:
    with st.sidebar:
        st.header("🎛️ Filtros")
        modo = st.radio("Ver datos como:", ["Resumen Mensual (Cierres)", "Detalle Semanal (Avance)"], index=1)
        
        anios_sel = st.multiselect("Años", sorted(df['Anio_V'].unique(), reverse=True), default=[2026, 2025])
        
        # Mapa de meses para el selector
        mes_labels = {1:'Ene', 2:'Feb', 3:'Mar', 4:'Abr', 5:'May', 6:'Jun', 7:'Jul', 8:'Ago', 9:'Set', 10:'Oct', 11:'Nov', 12:'Dic'}
        meses_disp = sorted(df['Mes_V'].unique())
        meses_sel = st.multiselect("Meses", meses_disp, default=meses_disp, format_func=lambda x: mes_labels.get(x, x))
        
        empresa_sel = st.selectbox("Seleccionar Empresa", ["Todas las Empresas"] + sorted(df['Empresa_V'].unique()))

    # --- FILTRADO DE DATA ---
    df_f = df[(df['Anio_V'].isin(anios_sel)) & (df['Mes_V'].isin(meses_sel))].copy()
    if empresa_sel != "Todas las Empresas":
        df_f = df_f[df_f['Empresa_V'] == empresa_sel]

    # Lógica de Semanas vs Totales
    if "Cierres" in modo:
        df_vis = df_f[df_f['Semana_V'].str.contains('total|Total', case=False, na=False)]
    else:
        # OJO: Mostramos todo lo que NO diga "Total" y que tenga algún dato de usabilidad > 0
        df_vis = df_f[~df_f['Semana_V'].str.contains('total|Total', case=False, na=False)]
        df_vis = df_vis[df_vis['Usabilidad_V'] > 0]

    st.title(f"📊 Reporte: {empresa_sel}")

    if not df_vis.empty:
        # Gráfica
        fig = go.Figure()
        for a in sorted(df_vis['Anio_V'].unique(), reverse=True):
            d = df_vis[df_vis['Anio_V'] == a].sort_values(['Mes_V', 'Semana_V'])
            # Eje X combinado
            x_labels = [f"{mes_labels.get(row.Mes_V)}-{row.Semana_V}" for _, row in d.iterrows()]
            
            fig.add_trace(go.Scatter(
                x=x_labels, y=d['Usabilidad_V'], name=f"Año {a}",
                mode='lines+markers+text', text=[f"{v:.1%}" for v in d['Usabilidad_V']],
                textposition="top center"
            ))
        
        fig.update_layout(yaxis=dict(tickformat=".0%", range=[0, 1.1]), height=500, paper_bgcolor='rgba(0,0,0,0)')
        st.plotly_chart(fig, use_container_width=True)
        
        # TABLA DE AUDITORÍA (Aquí DEBE aparecer febrero)
        st.markdown("### 📝 Detalle de registros encontrados")
        st.dataframe(df_vis[['Empresa_V', 'Anio_V', 'Mes_V', 'Semana_V', 'Usabilidad_V']])
    else:
        st.warning("⚠️ No se encuentran datos para los filtros seleccionados. Asegúrate de que en el Excel las filas de febrero tengan un valor en la columna H (% Usabilidad).")
