import streamlit as st
import pandas as pd
import plotly.graph_objects as go

# Configuración de página
st.set_page_config(page_title="Holos | BI", layout="wide")

# Enlaces de datos
LINK_1 = "https://docs.google.com/spreadsheets/d/e/2PACX-1vSWiXR7BLxwzX2wtD_uF59pvxtus8BL5iqgymKSh2-Llwt6smOJzR7ROUxICr57DA/pub?gid=1638907402&single=true&output=csv"
LINK_2 = "https://docs.google.com/spreadsheets/d/e/2PACX-1vSWiXR7BLxwzX2wtD_uF59pvxtus8BL5iqgymKSh2-Llwt6smOJzR7ROUxICr57DA/pub?gid=1341962834&single=true&output=csv"

# Colores Holos
SKY, LEAF, SEA, CORAL, BLACK = "#D1E9F6", "#F1FB8C", "#A9C1F5", "#FF9F86", "#000000"

@st.cache_data(ttl=30)
def cargar_data():
    try:
        # Carga y limpieza básica
        df1 = pd.read_csv(LINK_1)
        df2 = pd.read_csv(LINK_2)
        df = pd.concat([df1, df2], ignore_index=True)
        df.columns = [str(c).strip() for c in df.columns]
        
        # Identificación de columnas por posición o nombre (más robusto)
        # Buscamos la columna H (índice 7) o la que contenga el símbolo %
        c_usa = next((c for c in df.columns if '%' in c or 'Usabilidad' in c), df.columns[7])
        c_emp = next((c for c in df.columns if 'Empresa' in c), df.columns[0])
        c_mes = next((c for c in df.columns if 'Mes' in c and 'total' not in c.lower()), df.columns[2])
        c_ani = next((c for c in df.columns if 'Año' in c or 'Anio' in c), df.columns[11])

        def limpiar_porcentaje(val):
            try:
                if pd.isna(val): return 0.0
                s = str(val).replace('%', '').replace(',', '.').strip()
                n = float(s)
                # Si el número es > 1 (ej. 35.92), lo dividimos por 100
                return n / 100.0 if n > 1.1 else n
            except: return 0.0

        df['Usabilidad_V'] = df[c_usa].apply(limpiar_porcentaje)
        df['Anio_V'] = pd.to_numeric(df[c_ani], errors='coerce').fillna(0).astype(int)
        df['Mes_V'] = pd.to_numeric(df[c_mes], errors='coerce').fillna(0).astype(int)
        df['Empresa_V'] = df[c_emp].astype(str).str.strip()
        
        return df
    except Exception as e:
        st.error(f"Error técnico: {e}")
        return pd.DataFrame()

df = cargar_data()

if not df.empty:
    with st.sidebar:
        st.header("Filtros")
        empresas = sorted([e for e in df['Empresa_V'].unique() if str(e) != 'nan'])
        empresa_sel = st.selectbox("Empresa Target", ["Todas las Empresas"] + empresas)
        anios_sel = st.multiselect("Años", sorted(df['Anio_V'].unique(), reverse=True), default=[2025, 2026])
        meses_map = {1:'Ene', 2:'Feb', 3:'Mar', 4:'Abr', 5:'May', 6:'Jun', 7:'Jul', 8:'Ago', 9:'Set', 10:'Oct', 11:'Nov', 12:'Dic'}
        meses_sel = st.multiselect("Meses", sorted(meses_map.keys()), default=list(meses_map.keys()), format_func=lambda x: meses_map[x])

    st.title(f"Reporte: {empresa_sel}")

    # Filtrado dinámico
    mask = (df['Anio_V'].isin(anios_sel)) & (df['Mes_V'].isin(meses_sel))
    df_f = df[mask].copy()

    if empresa_sel != "Todas las Empresas":
        df_f = df_f[df_f['Empresa_V'] == empresa_sel]

    # --- MÉTRICAS (Gauges) ---
    anios_activos = sorted(df_f['Anio_V'].unique())
    colores = {2024: LEAF, 2025: CORAL, 2026: SEA}
    
    if anios_activos:
        cols = st.columns(len(anios_activos))
        for i, anio in enumerate(anios_activos):
            with cols[i]:
                # Aquí está el truco: promedio simple de la columna de porcentajes
                val = df_f[df_f['Anio_V'] == anio]['Usabilidad_V'].mean()
                
                fig = go.Figure(go.Indicator(
                    mode="gauge+number", value=val*100,
                    number={'suffix': "%", 'valueformat': '.2f'},
                    title={'text': f"Media {anio}"},
                    gauge={'axis': {'range': [0, 100]}, 'bar': {'color': BLACK},
                           'steps': [{'range': [0, 100], 'color': colores.get(anio, SKY)}]}
                ))
                fig.update_layout(height=260, margin=dict(l=20, r=20, t=40, b=20))
                st.plotly_chart(fig, use_container_width=True, key=f"gauge_{anio}")

    # --- GRÁFICA DE LÍNEAS ---
    st.subheader("Curva de Engagement")
    df_ev = df_f.groupby(['Anio_V', 'Mes_V'])['Usabilidad_V'].mean().reset_index()
    
    fig_l = go.Figure()
    for anio in anios_activos:
        df_p = df_ev[df_ev['Anio_V'] == anio].sort_values('Mes_V')
        fig_l.add_trace(go.Scatter(
            x=[meses_map[m] for m in df_p['Mes_V']], y=df_p['Usabilidad_V'],
            name=str(anio), mode='lines+markers+text',
            text=[f"{v:.1%}" for v in df_p['Usabilidad_V']], textposition="top center",
            line=dict(color=colores.get(anio, BLACK), width=3)
        ))
    fig_l.update_layout(yaxis=dict(tickformat=".0%", range=[0, 1.1]), height=400)
    st.plotly_chart(fig_l, use_container_width=True)

    # Tabla de comprobación para tu tranquilidad
    with st.expander("Verificar datos de la selección"):
        st.dataframe(df_f[['Empresa_V', 'Anio_V', 'Mes_V', 'Usabilidad_V']])
