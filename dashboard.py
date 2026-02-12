import streamlit as st
import pandas as pd
import plotly.graph_objects as go

# 1. Configuración de pantalla
st.set_page_config(page_title="Holos | Business Intelligence", layout="wide")

LINK_1 = "https://docs.google.com/spreadsheets/d/e/2PACX-1vSWiXR7BLxwzX2wtD_uF59pvxtus8BL5iqgymKSh2-Llwt6smOJzR7ROUxICr57DA/pub?gid=1638907402&single=true&output=csv"
LINK_2 = "https://docs.google.com/spreadsheets/d/e/2PACX-1vSWiXR7BLxwzX2wtD_uF59pvxtus8BL5iqgymKSh2-Llwt6smOJzR7ROUxICr57DA/pub?gid=1341962834&single=true&output=csv"

# --- ESTÉTICA HOLOS ---
SKY, LEAF, SEA, CORAL, BLACK, WHITE = "#D1E9F6", "#F1FB8C", "#A9C1F5", "#FF9F86", "#000000", "#FFFFFF"

st.markdown(f"""
    <style>
        .stApp {{ background-color: {SKY}; }}
        h1, h2, h3 {{ font-family: 'Philosopher', sans-serif !important; color: {BLACK}; }}
        .insight-card {{ background-color: {WHITE}; border-left: 6px solid {LEAF}; padding: 20px; border-radius: 10px; color: black; }}
    </style>
""", unsafe_allow_html=True)

@st.cache_data(ttl=5) # Actualización casi instantánea
def cargar_data():
    try:
        df1 = pd.read_csv(LINK_1)
        df2 = pd.read_csv(LINK_2)
        df = pd.concat([df1, df2], ignore_index=True)
        df.columns = [str(c).strip() for c in df.columns]
        
        # Limpieza de Usabilidad (Columna G - Índice 7)
        def limpiar_u(x):
            try:
                txt = str(x).replace('%', '').replace(',', '.').strip()
                val = float(txt)
                return val/100 if val > 1.1 else val
            except: return None

        df['Usabilidad_V'] = df.iloc[:, 7].apply(limpiar_u)
        df['Mes_V'] = pd.to_numeric(df.iloc[:, 9], errors='coerce').fillna(0).astype(int)
        df['Anio_V'] = pd.to_numeric(df.iloc[:, 11], errors='coerce').fillna(0).astype(int)
        df['Semana_V'] = df.iloc[:, 1].astype(str).str.strip()
        df['Empresa_V'] = df.iloc[:, 0].astype(str).str.strip()
        
        # IMPORTANTE: No borramos nada, solo filtramos años válidos
        return df[df['Anio_V'] >= 2025]
    except:
        return pd.DataFrame()

df = cargar_data()

if not df.empty:
    with st.sidebar:
        st.header("🎛️ Filtros")
        empresa_sel = st.selectbox("Empresa", ["Todas las Empresas"] + sorted(df['Empresa_V'].unique().tolist()))
        anios_sel = st.multiselect("Años", [2026, 2025], default=[2026, 2025])
        meses_map = {1:'Ene', 2:'Feb', 3:'Mar', 4:'Abr', 5:'May', 6:'Jun'}
        meses_sel = st.multiselect("Meses", [1, 2], default=[1, 2], format_func=lambda x: meses_map.get(x))

    st.markdown(f"<h1>📊 Reporte de Usabilidad: {empresa_sel}</h1>", unsafe_allow_html=True)

    # Filtro de los datos
    df_f = df[(df['Anio_V'].isin(anios_sel)) & (df['Mes_V'].isin(meses_sel))].copy()
    if empresa_sel != "Todas las Empresas":
        df_f = df_f[df_f['Empresa_V'] == empresa_sel]

    # --- GAUGES (PROMEDIO REAL) ---
    anios_activos = sorted(df_f['Anio_V'].unique())
    if anios_activos:
        cols = st.columns(len(anios_activos))
        for i, a in enumerate(anios_activos):
            val = df_f[df_f['Anio_V'] == a]['Usabilidad_V'].mean()
            with cols[i]:
                fig = go.Figure(go.Indicator(
                    mode="gauge+number", value=(val or 0)*100,
                    number={'suffix': "%", 'valueformat': '.1f'},
                    title={'text': f"Media {a}"},
                    gauge={'axis': {'range': [0, 100]}, 'bar': {'color': BLACK},
                           'steps': [{'range': [0, 100], 'color': SEA if a==2026 else CORAL}]}
                ))
                fig.update_layout(height=200, margin=dict(l=20, r=20, t=40, b=20), paper_bgcolor='rgba(0,0,0,0)')
                st.plotly_chart(fig, use_container_width=True, key=f"g_{a}")

    # --- CURVA DE AVANCE (ESTA ES LA CLAVE) ---
    st.markdown("### 📈 Avance Mensual y Semanal")
    
    # Creamos un ranking para ordenar: Semanas del 1 al 4, y luego el Total
    def asignar_orden(row):
        sem = str(row['Semana_V']).lower()
        if '1era' in sem: return 1
        if '2da' in sem: return 2
        if '3era' in sem: return 3
        if '4ta' in sem: return 4
        return 5 # Para "Mes total" o cualquier otro dato del mes

    df_f['Orden'] = df_f.apply(asignar_orden, axis=1)
    
    # Agrupamos para limpiar duplicados y asegurar que Febrero aparezca
    df_plot = df_f.groupby(['Anio_V', 'Mes_V', 'Semana_V', 'Orden'])['Usabilidad_V'].mean().reset_index()
    df_plot = df_plot.sort_values(['Anio_V', 'Mes_V', 'Orden'])

    if not df_plot.empty:
        fig_line = go.Figure()
        for a in sorted(anios_sel):
            d = df_plot[df_plot['Anio_V'] == a]
            if not d.empty:
                # ETIQUETA DINÁMICA: Si es el orden 5, mostramos "TOTAL [MES]"
                labels = [f"{meses_map.get(m)} - {s}" for m, s in zip(d['Mes_V'], d['Semana_V'])]
                
                fig_line.add_trace(go.Scatter(
                    x=labels, y=d['Usabilidad_V'],
                    name=f"Año {a}", mode='lines+markers+text',
                    text=[f"{v:.1%}" if pd.notnull(v) else "" for v in d['Usabilidad_V']],
                    textposition="top center",
                    line=dict(width=4, color=SEA if a==2026 else CORAL),
                    connectgaps=True
                ))

        fig_line.update_layout(
            yaxis=dict(tickformat=".0%", range=[0, 1.1]),
            xaxis=dict(tickangle=-45),
            margin=dict(l=0, r=0, t=30, b=0),
            height=450, paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)'
        )
        st.plotly_chart(fig_line, use_container_width=True)

    # --- INFORME ---
    st.markdown(f"""
    <div class='insight-card'>
        <strong>Informe de Avance:</strong> El sistema ha detectado datos para <b>Enero</b> y <b>Febrero</b>.<br>
        La curva muestra el progreso desde la semana 1 hasta el cierre mensual, conectando con el avance actual de 2026.
    </div>
    """, unsafe_allow_html=True)

    with st.expander("📂 Ver Data Cruda (Para verificar por qué no sale algo)"):
        st.dataframe(df_f[['Empresa_V', 'Anio_V', 'Mes_V', 'Semana_V', 'Usabilidad_V']])
else:
    st.error("No hay conexión con el Excel. Asegúrate de que esté 'Publicado en la Web' como CSV.")
