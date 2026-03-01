import streamlit as st
import pandas as pd
import plotly.graph_objects as go

# 1. Configuración de pantalla
st.set_page_config(page_title="Holos | BI Final", layout="wide")

LINK_1 = "https://docs.google.com/spreadsheets/d/e/2PACX-1vSWiXR7BLxwzX2wtD_uF59pvxtus8BL5iqgymKSh2-Llwt6smOJzR7ROUxICr57DA/pub?gid=1638907402&single=true&output=csv"
LINK_2 = "https://docs.google.com/spreadsheets/d/e/2PACX-1vSWiXR7BLxwzX2wtD_uF59pvxtus8BL5iqgymKSh2-Llwt6smOJzR7ROUxICr57DA/pub?gid=1341962834&single=true&output=csv"

SKY, LEAF, SEA, CORAL, BLACK = "#D1E9F6", "#F1FB8C", "#A9C1F5", "#FF9F86", "#000000"

st.markdown(f"""
    <style>
        .stApp {{ background-color: {SKY}; }}
        h1, h2, h3 {{ font-family: 'Philosopher', sans-serif !important; color: {BLACK}; }}
        .insight-card {{ background-color: #FFFFFF; border-left: 6px solid {LEAF}; padding: 20px; border-radius: 10px; color: black; }}
    </style>
""", unsafe_allow_html=True)

@st.cache_data(ttl=10)
def cargar_data_robusta():
    def procesar(url):
        try:
            raw = pd.read_csv(url)
            # Creamos un DF limpio basado en POSICIÓN, no en nombres
            df_lp = pd.DataFrame()
            df_lp['Empresa'] = raw.iloc[:, 0].astype(str).str.strip() # Col A
            df_lp['Semana'] = raw.iloc[:, 1].astype(str).str.strip()  # Col B
            
            def to_pct(x):
                try:
                    v = str(x).replace('%', '').replace(',', '.').strip()
                    n = float(v)
                    return n/100 if n > 1.1 else n
                except: return None
            
            df_lp['Usabilidad'] = raw.iloc[:, 7].apply(to_pct) # Col H
            df_lp['Mes'] = pd.to_numeric(raw.iloc[:, 9], errors='coerce') # Col J
            df_lp['Anio'] = pd.to_numeric(raw.iloc[:, 11], errors='coerce') # Col L
            return df_lp.dropna(subset=['Usabilidad'])
        except:
            return pd.DataFrame()

    d1 = procesar(LINK_1)
    d2 = procesar(LINK_2)
    final = pd.concat([d1, d2], ignore_index=True)
    return final

df = cargar_data_robusta()

if not df.empty:
    with st.sidebar:
        st.header("🎛️ Filtros")
        # Aseguramos que detecte 2026
        anios_reales = sorted(df['Anio'].unique().astype(int).tolist(), reverse=True)
        anios_sel = st.multiselect("Años", anios_reales, default=anios_reales)
        
        empresas = sorted(df['Empresa'].unique().tolist())
        emp_sel = st.selectbox("Empresa", ["Todas las Empresas"] + empresas)
        
        meses_sel = st.multiselect("Meses", [1, 2, 3], default=[1, 2], format_func=lambda x: {1:'Ene', 2:'Feb', 3:'Mar'}.get(x))

    st.markdown(f"<h1>📊 Reporte Consolidado: {emp_sel}</h1>", unsafe_allow_html=True)

    # Filtrado
    df_f = df[df['Anio'].isin(anios_sel) & df['Mes'].isin(meses_sel)].copy()
    if emp_sel != "Todas las Empresas":
        df_f = df_f[df_f['Empresa'] == emp_sel]

    # --- GAUGES ---
    if not df_f.empty:
        cols = st.columns(len(anios_sel))
        for i, a in enumerate(sorted(anios_sel)):
            val = df_f[df_f['Anio'] == a]['Usabilidad'].mean()
            with cols[i]:
                fig = go.Figure(go.Indicator(
                    mode="gauge+number", value=(val or 0)*100,
                    number={'suffix': "%", 'valueformat': '.1f'},
                    title={'text': f"Media {a}"},
                    gauge={'axis': {'range': [0, 100]}, 'bar': {'color': BLACK},
                           'steps': [{'range': [0, 100], 'color': SEA if a==2026 else CORAL}]}
                ))
                fig.update_layout(height=200, margin=dict(l=20, r=20, t=40, b=20), paper_bgcolor='rgba(0,0,0,0)')
                st.plotly_chart(fig, use_container_width=True)

    # --- CURVA DE AVANCE ---
    st.markdown("### 📈 Curva de Engagement (Ene - Feb)")
    
    # Agrupamos para calcular el punto del mes (si no hay cierre, promedia semanas)
    df_plot = df_f.groupby(['Anio', 'Mes'])['Usabilidad'].mean().reset_index()
    df_plot = df_plot.sort_values(['Anio', 'Mes'])

    fig_l = go.Figure()
    mes_nom = {1:'Ene', 2:'Feb', 3:'Mar'}
    
    for a in sorted(anios_sel):
        d = df_plot[df_plot['Anio'] == a]
        if not d.empty:
            fig_l.add_trace(go.Scatter(
                x=[mes_nom.get(m) for m in d['Mes']], y=d['Usabilidad'],
                name=f"Año {a}", mode='lines+markers+text',
                text=[f"{v:.1%}" for v in d['Usabilidad']],
                textposition="top center",
                line=dict(width=4, color=SEA if a==2026 else CORAL)
            ))

    fig_l.update_layout(yaxis=dict(tickformat=".0%", range=[0, 1.1]), height=400, paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)')
    st.plotly_chart(fig_l, use_container_width=True)

    # Auditoría visual rápida para tu reunión
    with st.expander("🔍 Verificar carga de 2026"):
        st.write("Datos encontrados de 2026:", len(df[df['Anio'] == 2026]))
        st.dataframe(df[df['Anio'] == 2026].head())

else:
    st.error("No se detectan datos. Revisa que AMBAS pestañas estén publicadas como CSV.")
