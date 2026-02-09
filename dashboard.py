import streamlit as st
import pandas as pd
import plotly.graph_objects as go

st.set_page_config(page_title="Holos | BI Dashboard", layout="wide")

LINK_1 = "https://docs.google.com/spreadsheets/d/e/2PACX-1vSWiXR7BLxwzX2wtD_uF59pvxtus8BL5iqgymKSh2-Llwt6smOJzR7ROUxICr57DA/pub?gid=1638907402&single=true&output=csv"
LINK_2 = "https://docs.google.com/spreadsheets/d/e/2PACX-1vSWiXR7BLxwzX2wtD_uF59pvxtus8BL5iqgymKSh2-Llwt6smOJzR7ROUxICr57DA/pub?gid=1341962834&single=true&output=csv"

@st.cache_data(ttl=2)
def cargar_todo():
    try:
        # Cargamos y limpiamos filas totalmente vacías
        df1 = pd.read_csv(LINK_1).dropna(subset=['Nombre de la Empresa'], errors='ignore')
        df2 = pd.read_csv(LINK_2).dropna(subset=['Nombre de la Empresa'], errors='ignore')
        df = pd.concat([df1, df2], ignore_index=True)
        
        # Limpiamos nombres de columnas
        df.columns = [str(c).strip() for c in df.columns]

        # CREACIÓN FORZOSA DE COLUMNAS (Para evitar el KeyError)
        # Si no encuentra 'Inicio del Año', usa la columna 11 por posición
        col_year = "Inicio del Año" if "Inicio del Año" in df.columns else df.columns[11]
        col_month = "Inicio del Mes" if "Inicio del Mes" in df.columns else df.columns[9]
        col_usa = "% Usabilidad/Engagement" if "% Usabilidad/Engagement" in df.columns else df.columns[7]
        
        df['Anio_V'] = pd.to_numeric(df[col_year], errors='coerce').fillna(0).astype(int)
        df['Mes_V'] = pd.to_numeric(df[col_month], errors='coerce').fillna(0).astype(int)
        df['Usabilidad_V'] = pd.to_numeric(df[col_usa].astype(str).str.replace('%','').str.replace(',','.'), errors='coerce').fillna(0)
        
        # Normalizar porcentaje
        df['Usabilidad_V'] = df['Usabilidad_V'].apply(lambda x: x/100 if x > 1.1 else x)
        
        df['Empresa_V'] = df['Nombre de la Empresa'].astype(str).str.strip()
        df['Semana_V'] = df['Semana'].astype(str).str.strip()
        
        return df[df['Anio_V'] > 0] # Solo filas con año válido
    except Exception as e:
        # Si algo falla, devolvemos un DataFrame mínimo para que no crashee
        return pd.DataFrame(columns=['Anio_V', 'Mes_V', 'Empresa_V', 'Semana_V', 'Usabilidad_V'])

df = cargar_todo()

# --- INTERFAZ SIN CRASHEOS ---
if not df.empty:
    with st.sidebar:
        st.header("🎛️ Filtros")
        modo = st.radio("Modo:", ["Resumen Mensual", "Detalle Semanal"], index=1)
        
        # Filtros con valores seguros
        anios_disp = sorted(df['Anio_V'].unique(), reverse=True)
        anios_sel = st.multiselect("Años", anios_disp, default=[2026] if 2026 in anios_disp else anios_disp)
        
        mes_map = {1:'Ene', 2:'Feb', 3:'Mar', 4:'Abr', 5:'May', 6:'Jun', 7:'Jul', 8:'Ago', 9:'Set', 10:'Oct', 11:'Nov', 12:'Dic'}
        meses_sel = st.multiselect("Meses", sorted(df['Mes_V'].unique()), default=[1, 2], format_func=lambda x: mes_map.get(x, x))
        
        empresa_sel = st.selectbox("Empresa", ["Todas"] + sorted(df['Empresa_V'].unique()))

    # Filtrado final
    mask = (df['Anio_V'].isin(anios_sel)) & (df['Mes_V'].isin(meses_sel))
    if empresa_sel != "Todas":
        mask = mask & (df['Empresa_V'] == empresa_sel)
    
    df_f = df[mask].copy()

    # Separar Semanas vs Totales
    if "Mensual" in modo:
        df_vis = df_f[df_f['Semana_V'].str.contains('total', case=False, na=False)]
    else:
        df_vis = df_f[~df_f['Semana_V'].str.contains('total', case=False, na=False)]

    st.title(f"📊 Reporte: {empresa_sel}")

    if not df_vis.empty:
        fig = go.Figure()
        for a in sorted(df_vis['Anio_V'].unique()):
            d = df_vis[df_vis['Anio_V'] == a].sort_values(['Mes_V', 'Semana_V'])
            # Evitar promedios si hay varias empresas, mostrar evolución
            d_plot = d.groupby(['Mes_V', 'Semana_V'])['Usabilidad_V'].mean().reset_index()
            x_labels = [f"{mes_map.get(m)}-{s}" for m, s in zip(d_plot['Mes_V'], d_plot['Semana_V'])]
            
            fig.add_trace(go.Scatter(x=x_labels, y=d_plot['Usabilidad_V'], name=f"Año {a}", mode='lines+markers+text',
                                     text=[f"{v:.1%}" for v in d_plot['Usabilidad_V']], textposition="top center"))
        
        fig.update_layout(yaxis=dict(tickformat=".0%", range=[0, 1.1]))
        st.plotly_chart(fig, use_container_width=True)
        
        # TABLA DE VERIFICACIÓN
        with st.expander("👀 Ver datos cargados (Revisa si aparece Mes 2)"):
            st.dataframe(df_vis[['Empresa_V', 'Anio_V', 'Mes_V', 'Semana_V', 'Usabilidad_V']])
    else:
        st.warning("No hay datos. Asegúrate de que en el Excel las filas de febrero tengan un '2' en la columna J.")
else:
    st.error("Esperando conexión con Excel... (Asegúrate de que el archivo esté Publicado en la Web como CSV)")
