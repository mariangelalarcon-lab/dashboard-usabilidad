import streamlit as st
import pandas as pd
import plotly.graph_objects as go

# Configuración profesional
st.set_page_config(page_title="Holos BI - Fixed", layout="wide")

LINK_1 = "https://docs.google.com/spreadsheets/d/e/2PACX-1vSWiXR7BLxwzX2wtD_uF59pvxtus8BL5iqgymKSh2-Llwt6smOJzR7ROUxICr57DA/pub?gid=1638907402&single=true&output=csv"
LINK_2 = "https://docs.google.com/spreadsheets/d/e/2PACX-1vSWiXR7BLxwzX2wtD_uF59pvxtus8BL5iqgymKSh2-Llwt6smOJzR7ROUxICr57DA/pub?gid=1341962834&single=true&output=csv"

@st.cache_data(ttl=60)
def load_data_perfect():
    try:
        df1 = pd.read_csv(LINK_1)
        df2 = pd.read_csv(LINK_2)
        df = pd.concat([df1, df2], ignore_index=True)
        df.columns = [str(c).strip() for c in df.columns]

        # 1. Identificación manual por posición (basado en tu captura de Excel)
        # Columna H (index 7) es Usabilidad. Columna A (index 0) es Empresa.
        df['Empresa_V'] = df.iloc[:, 0].astype(str).str.strip()
        df['Semana_V'] = df.iloc[:, 1].astype(str).str.strip()
        df['Mes_V'] = pd.to_numeric(df.iloc[:, 8], errors='coerce').fillna(0).astype(int) # Columna I/J aprox
        df['Anio_V'] = pd.to_numeric(df.iloc[:, 11], errors='coerce').fillna(0).astype(int) # Columna L aprox

        # 2. Limpieza de Porcentajes (Columna H - index 7)
        def clean_pct(x):
            try:
                val = str(x).replace('%', '').replace(',', '.').strip()
                return float(val) / 100.0 if float(val) > 1.1 else float(val)
            except: return 0.0
        
        df['Valor_Real'] = df.iloc[:, 7].apply(clean_pct)

        # 3. Filtro de Seguridad (Adiós 1899 y Nans)
        df = df[(df['Anio_V'] >= 2023) & (df['Anio_V'] <= 2026)].copy()
        df = df[df['Empresa_V'].str.lower() != 'nan'].copy()
        
        return df
    except Exception as e:
        st.error(f"Error de estructura: {e}")
        return pd.DataFrame()

df = load_data_perfect()

if not df.empty:
    # --- SIDEBAR ---
    with st.sidebar:
        st.title("⚙️ Filtros")
        modo = st.radio("Ver datos por:", ["Resumen Mensual (Cierre)", "Detalle Semanal"])
        
        emp_sel = st.selectbox("Empresa Target", ["Todas las Empresas"] + sorted(df['Empresa_V'].unique()))
        
        anios_sel = st.multiselect("Años", sorted(df['Anio_V'].unique(), reverse=True), default=[2025, 2026])
        
        meses_map = {1:'Ene', 2:'Feb', 3:'Mar', 4:'Abr', 5:'May', 6:'Jun', 7:'Jul', 8:'Ago', 9:'Set', 10:'Oct', 11:'Nov', 12:'Dic'}
        meses_sel = st.multiselect("Meses", sorted(meses_map.keys()), default=list(meses_map.keys()), format_func=lambda x: meses_map[x])

    # --- LÓGICA DE FILTRADO ---
    df_f = df[(df['Anio_V'].isin(anios_sel)) & (df['Mes_V'].isin(meses_sel))].copy()

    if modo == "Resumen Mensual (Cierre)":
        df_vis = df_f[df_f['Semana_V'].str.contains('total|Total', na=False)]
    else:
        df_vis = df_f[~df_f['Semana_V'].str.contains('total|Total', na=False)]

    if emp_sel != "Todas las Empresas":
        df_vis = df_vis[df_vis['Empresa_V'] == emp_sel]

    # --- VISUALIZACIÓN ---
    st.title(f"📊 Reporte: {emp_sel}")
    
    # 1. MÉTRICAS PRINCIPALES (GAUGES)
    anios_activos = sorted(df_vis['Anio_V'].unique())
    cols = st.columns(len(anios_activos) if anios_activos else 1)
    
    colors = {2023: "#E5E7E9", 2024: "#F1FB8C", 2025: "#FF9F86", 2026: "#A9C1F5"}

    for i, a in enumerate(anios_activos):
        # Aquí calculamos la media exacta:
        # Si es una empresa, da su valor. Si son todas, da el 32.72%
        val_anio = df_vis[df_vis['Anio_V'] == a]['Valor_Real'].mean()
        
        with cols[i]:
            fig = go.Figure(go.Indicator(
                mode="gauge+number", value=val_anio*100,
                number={'suffix': "%", 'valueformat': '.2f', 'font': {'color': 'black'}},
                title={'text': f"Media {a}", 'font': {'size': 20}},
                gauge={'axis': {'range': [0, 100]}, 'bar': {'color': 'black'},
                       'steps': [{'range': [0, 100], 'color': colors.get(a, "#D1E9F6")}]}
            ))
            fig.update_layout(height=250, margin=dict(l=30,r=30,t=50,b=20), paper_bgcolor='white')
            st.plotly_chart(fig, use_container_width=True, key=f"gauge_{a}")

    # 2. GRÁFICA DE TENDENCIA (UNA SOLA LÍNEA)
    st.subheader(f"📈 Curva de Engagement ({modo})")
    
    # Agrupamos por Mes y Año para tener una sola línea por año, no una por empresa
    df_chart = df_vis.groupby(['Anio_V', 'Mes_V', 'Semana_V'])['Valor_Real'].mean().reset_index()
    
    fig_line = go.Figure()
    for a in anios_activos:
        df_p = df_chart[df_chart['Anio_V'] == a].sort_values(['Mes_V', 'Semana_V'])
        
        x_labels = [f"{meses_map.get(m, m)}-{s[:3]}" for m, s in zip(df_p['Mes_V'], df_p['Semana_V'])]
        
        fig_line.add_trace(go.Scatter(
            x=x_labels, y=df_p['Valor_Real'], name=f"Año {a}",
            mode='lines+markers+text',
            text=[f"{v:.1%}" for v in df_p['Valor_Real']], textposition="top center",
            line=dict(color=colors.get(a, "black"), width=4)
        ))

    fig_line.update_layout(yaxis=dict(tickformat=".0%", range=[0, 1.1]), height=450, 
                          hovermode="x unified", paper_bgcolor='white', plot_bgcolor='white')
    fig_line.update_xaxes(showgrid=True, gridcolor='#EEE')
    fig_line.update_yaxes(showgrid=True, gridcolor='#EEE')
    st.plotly_chart(fig_line, use_container_width=True)

    # 3. TABLA DE CONTROL (Para validar contra el Excel)
    with st.expander("📝 Tabla de Validación (Compara estos datos con tu Excel)"):
        st.write("Estos son los valores que el sistema está leyendo de la columna H:")
        st.dataframe(df_vis[['Empresa_V', 'Anio_V', 'Mes_V', 'Semana_V', 'Valor_Real']].sort_values(['Anio_V', 'Mes_V']))

else:
    st.error("No se pudieron cargar los datos. Revisa que el Excel no esté bloqueado o vacío.")
