import streamlit as st
import pandas as pd
import plotly.graph_objects as go

# 1. Configuración Pro
st.set_page_config(page_title="Holos | BI Dashboard", layout="wide")

# --- ENLACES CORREGIDOS (Verificar GID de cada hoja) ---
LINK_HOJA_1 = "https://docs.google.com/spreadsheets/d/e/2PACX-1vSWiXR7BLxwzX2wtD_uF59pvxtus8BL5iqgymKSh2-Llwt6smOJzR7ROUxICr57DA/pub?gid=1638907402&single=true&output=csv"
LINK_HOJA_2 = "https://docs.google.com/spreadsheets/d/e/2PACX-1vSWiXR7BLxwzX2wtD_uF59pvxtus8BL5iqgymKSh2-Llwt6smOJzR7ROUxICr57DA/pub?gid=1341962834&single=true&output=csv"

# --- PALETA HOLOS ---
SKY, LEAF, SEA, CORAL, BLACK = "#D1E9F6", "#F1FB8C", "#A9C1F5", "#FF9F86", "#000000"

@st.cache_data(ttl=5)
def cargar_unificado():
    try:
        # Leer ambas pestañas
        df1 = pd.read_csv(LINK_HOJA_1)
        df2 = pd.read_csv(LINK_HOJA_2)
        
        # Unificar
        df = pd.concat([df1, df2], ignore_index=True)
        df.columns = [str(c).strip() for c in df.columns]
        
        # Mapeo por posición para evitar fallos si cambias un nombre en el Excel
        res = pd.DataFrame()
        res['Empresa'] = df.iloc[:, 0].astype(str).str.strip()
        res['Semana'] = df.iloc[:, 1].astype(str).str.strip()
        
        def clean_num(x):
            try:
                v = float(str(x).replace('%', '').replace(',', '.').strip())
                return v/100 if v > 1.1 else v
            except: return None

        res['Usabilidad'] = df.iloc[:, 7].apply(clean_num) # Columna G
        res['Mes'] = pd.to_numeric(df.iloc[:, 9], errors='coerce').fillna(0).astype(int) # Columna J
        res['Anio'] = pd.to_numeric(df.iloc[:, 11], errors='coerce').fillna(0).astype(int) # Columna L
        
        # Filtro de seguridad
        return res.dropna(subset=['Usabilidad'])
    except Exception as e:
        st.error(f"Error unificando hojas: {e}")
        return pd.DataFrame()

df_total = cargar_unificado()

if not df_total.empty:
    with st.sidebar:
        st.header("🎛️ Filtros de Control")
        empresa_sel = st.selectbox("Seleccionar Empresa", ["Todas las Empresas"] + sorted(df_total['Empresa'].unique()))
        anios_sel = st.multiselect("Años", [2026, 2025], default=[2026, 2025])
        
        meses_nombres = {1:'Ene', 2:'Feb', 3:'Mar', 4:'Abr', 5:'May', 6:'Jun'}
        meses_sel = st.multiselect("Meses", [1, 2], default=[1, 2], format_func=lambda x: meses_nombres.get(x))

    # Título Estilo Holos
    st.markdown(f"<h1 style='color:{BLACK};'>📊 Reporte de Avance: {empresa_sel}</h1>", unsafe_allow_html=True)

    # Filtrado final
    mask = (df_total['Anio.isin(anios_sel)) & (df_total['Mes'].isin(meses_sel))
    if empresa_sel != "Todas las Empresas":
        mask &= (df_total['Empresa'] == empresa_sel)
    df_f = df_total[mask].copy()

    # --- GAUGES ---
    if not df_f.empty:
        g_cols = st.columns(len(anios_sel))
        for i, a in enumerate(sorted(anios_sel)):
            prom = df_f[df_f['Anio'] == a]['Usabilidad'].mean()
            with g_cols[i]:
                fig_g = go.Figure(go.Indicator(
                    mode="gauge+number", value=(prom or 0)*100,
                    number={'suffix': "%", 'valueformat': '.1f'},
                    title={'text': f"Media {a}"},
                    gauge={'axis': {'range': [0, 100]}, 'bar': {'color': BLACK},
                           'steps': [{'range': [0, 100], 'color': SEA if a==2026 else CORAL}]}
                ))
                fig_g.update_layout(height=200, margin=dict(l=20, r=20, t=40, b=20), paper_bgcolor='rgba(0,0,0,0)')
                st.plotly_chart(fig_g, use_container_width=True)

    # --- CURVA DE AVANCE CRONOLÓGICO ---
    st.markdown("### 📈 Progreso Semanal y Cierres Mensuales")
    
    # Sistema de Ranking para que el gráfico no "salte"
    def rankear(s):
        s = s.lower()
        if '1era' in s: return 1
        if '2da' in s: return 2
        if '3era' in s: return 3
        if '4ta' in s: return 4
        return 5 # "Mes total"

    df_f['Orden'] = df_f['Semana'].apply(rankear)
    
    # Agrupamos por si hay varias empresas en "Todas las Empresas"
    df_plot = df_f.groupby(['Anio', 'Mes', 'Semana', 'Orden'])['Usabilidad'].mean().reset_index()
    df_plot = df_plot.sort_values(['Anio', 'Mes', 'Orden'])

    if not df_plot.empty:
        fig_l = go.Figure()
        for a in sorted(anios_sel):
            d = df_plot[df_plot['Anio'] == a]
            if not d.empty:
                # Etiquetas del Eje X: Ene - 1era Semana... Ene - Mes Total
                etiquetas = [f"{meses_nombres.get(m)} - {s}" for m, s in zip(d['Mes'], d['Semana'])]
                
                fig_l.add_trace(go.Scatter(
                    x=etiquetas, y=d['Usabilidad'],
                    name=f"Año {a}", mode='lines+markers+text',
                    text=[f"{v:.1%}" for v in d['Usabilidad']],
                    textposition="top center",
                    line=dict(width=4, color=SEA if a==2026 else CORAL),
                    connectgaps=True
                ))

        fig_l.update_layout(
            yaxis=dict(tickformat=".0%", range=[0, 1.1], gridcolor="#eee"),
            xaxis=dict(tickangle=-45, showgrid=False),
            height=450, paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)',
            margin=dict(l=0, r=0, t=30, b=0)
        )
        st.plotly_chart(fig_l, use_container_width=True)

    # --- FOOTER DE IA ---
    if not df_f.empty:
        ult = df_f.sort_values(['Anio', 'Mes', 'Orden'], ascending=False).iloc[0]
        st.markdown(f"""
        <div style="background-color: white; border-left: 6px solid {LEAF}; padding: 20px; border-radius: 10px; color: black;">
            <strong>Diagnóstico Holos:</strong> Se ha validado la conexión con ambas hojas del Excel.<br>
            <strong>Avance detectado:</strong> El punto más reciente es <b>{ult['Semana']}</b> de <b>{meses_nombres.get(ult['Mes'])}</b> ({ult['Usabilidad']:.1%}).
        </div>
        """, unsafe_allow_html=True)

else:
    st.error("Error Crítico: No se pudo leer ninguna de las dos hojas. Revisa que ambas estén publicadas como CSV.")
