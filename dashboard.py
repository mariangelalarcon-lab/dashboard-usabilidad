import streamlit as st
import pandas as pd
import plotly.graph_objects as go

st.set_page_config(page_title="Holos | BI Dashboard", layout="wide")

# Enlaces directos
LINK_1 = "https://docs.google.com/spreadsheets/d/e/2PACX-1vSWiXR7BLxwzX2wtD_uF59pvxtus8BL5iqgymKSh2-Llwt6smOJzR7ROUxICr57DA/pub?gid=1638907402&single=true&output=csv"
LINK_2 = "https://docs.google.com/spreadsheets/d/e/2PACX-1vSWiXR7BLxwzX2wtD_uF59pvxtus8BL5iqgymKSh2-Llwt6smOJzR7ROUxICr57DA/pub?gid=1341962834&single=true&output=csv"

# Forzamos que NO use caché viejo para que agarre el "2" de febrero ahora mismo
@st.cache_data(ttl=1) 
def cargar_data_limpia():
    try:
        df1 = pd.read_csv(LINK_1)
        df2 = pd.read_csv(LINK_2)
        df = pd.concat([df1, df2], ignore_index=True)
        df.columns = [str(c).strip() for c in df.columns]

        # Mapeo según tu captura de Excel
        # Columna J = Inicio del Mes, Columna L = Inicio del Año, Columna H = % Usabilidad
        c_mes = next((c for c in df.columns if "Inicio del Mes" in c), "Inicio del Mes")
        c_ani = next((c for c in df.columns if "Inicio del Año" in c), "Inicio del Año")
        c_usa = next((c for c in df.columns if "%" in c), "% Usabilidad/Engagement")
        c_sem = "Semana"
        c_emp = "Nombre de la Empresa"

        # Conversión estricta
        df['Anio_V'] = pd.to_numeric(df[c_ani], errors='coerce').fillna(0).astype(int)
        df['Mes_V'] = pd.to_numeric(df[c_mes], errors='coerce').fillna(0).astype(int)
        df['Empresa_V'] = df[c_emp].astype(str).str.strip()
        df['Semana_V'] = df[c_sem].astype(str).str.strip()
        
        def to_f(val):
            try:
                s = str(val).replace('%', '').replace(',', '.').strip()
                n = float(s)
                return n / 100.0 if n > 1.1 else n
            except: return 0.0
        df['Usabilidad_V'] = df[c_usa].apply(to_f)
        
        # Filtramos filas vacías del Excel
        return df[df['Anio_V'] > 2020]
    except: return pd.DataFrame()

df = cargar_data_limpia()

# --- INTERFAZ ---
with st.sidebar:
    st.header("🎛️ Filtros")
    modo = st.radio("Modo:", ["Resumen Mensual", "Detalle Semanal"], index=1)
    # Selecciona 2026 primero
    anios_sel = st.multiselect("Años", sorted(df['Anio_V'].unique(), reverse=True), default=[2026, 2025])
    mes_map = {1:'Ene', 2:'Feb', 3:'Mar', 4:'Abr', 5:'May', 6:'Jun', 7:'Jul', 8:'Ago', 9:'Set', 10:'Oct', 11:'Nov', 12:'Dic'}
    meses_sel = st.multiselect("Meses", sorted(df['Mes_V'].unique()), default=[1, 2], format_func=lambda x: mes_map.get(x))
    empresa_sel = st.selectbox("Empresa", ["Todas las Empresas"] + sorted(df['Empresa_V'].unique()))

# --- PROCESAMIENTO ---
df_f = df[(df['Anio_V'].isin(anios_sel)) & (df['Mes_V'].isin(meses_sel))]
if empresa_sel != "Todas las Empresas":
    df_f = df_f[df_f['Empresa_V'] == empresa_sel]

# Separar Semanas de Totales
if "Mensual" in modo:
    df_vis = df_f[df_f['Semana_V'].str.contains('total', case=False, na=False)]
else:
    df_vis = df_f[~df_f['Semana_V'].str.contains('total', case=False, na=False)]

st.title(f"📊 Reporte: {empresa_sel}")

if not df_vis.empty:
    fig = go.Figure()
    # Dibujamos una línea por cada año para que NO se mezclen
    for anio in sorted(df_vis['Anio_V'].unique()):
        d_anio = df_vis[df_vis['Anio_V'] == anio].sort_values(['Mes_V', 'Semana_V'])
        # Agrupamos por semana para evitar duplicados si hay varias empresas
        d_plot = d_anio.groupby(['Mes_V', 'Semana_V'])['Usabilidad_V'].mean().reset_index()
        
        x_labels = [f"{mes_map.get(m)}-{s}" for m, s in zip(d_plot['Mes_V'], d_plot['Semana_V'])]
        fig.add_trace(go.Scatter(x=x_labels, y=d_plot['Usabilidad_V'], name=f"Año {anio}", mode='lines+markers'))

    fig.update_layout(yaxis=dict(tickformat=".1%", range=[0, 1.05]), height=450)
    st.plotly_chart(fig, use_container_width=True)

    st.markdown("### 🔍 Auditoría de Datos Seleccionados")
    st.write("Si aquí no ves el número '2' en la columna Mes_V, el Excel aún no se ha actualizado en la web.")
    st.dataframe(df_vis[['Empresa_V', 'Anio_V', 'Mes_V', 'Semana_V', 'Usabilidad_V']])
else:
    st.warning("No hay datos para mostrar con esos filtros.")
