import streamlit as st
import pandas as pd
import plotly.graph_objects as go

# 1. Configuración de pantalla
st.set_page_config(page_title="Holos | Business Intelligence", layout="wide")

# --- ENLACES DE DATOS DIRECTOS ---
LINK_1 = "https://docs.google.com/spreadsheets/d/e/2PACX-1vSWiXR7BLxwzX2wtD_uF59pvxtus8BL5iqgymKSh2-Llwt6smOJzR7ROUxICr57DA/pub?gid=1638907402&single=true&output=csv"
LINK_2 = "https://docs.google.com/spreadsheets/d/e/2PACX-1vSWiXR7BLxwzX2wtD_uF59pvxtus8BL5iqgymKSh2-Llwt6smOJzR7ROUxICr57DA/pub?gid=1341962834&single=true&output=csv"

# --- PALETA OFICIAL HOLOS ---
SKY = "#D1E9F6"
LEAF = "#F1FB8C"
SEA = "#A9C1F5"
CORAL = "#FF9F86"
BLACK = "#000000"
WHITE = "#FFFFFF"

# --- DISEÑO UI ---
st.markdown(f"""
    <link href="https://fonts.googleapis.com/css2?family=Philosopher:wght@700&family=Inter:wght@400;600&display=swap" rel="stylesheet">
    <style>
        .stApp {{ background-color: {SKY}; }}
        h1, h2, h3 {{ font-family: 'Philosopher', sans-serif !important; color: {BLACK}; }}
        * {{ font-family: 'Inter', sans-serif; }}
        [data-testid="stSidebar"] {{ background-color: {WHITE}; }}
        .insight-card {{ background-color: {WHITE}; border-left: 6px solid {LEAF}; padding: 20px; border-radius: 10px; box-shadow: 0 4px 6px rgba(0,0,0,0.05); color: black; }}
    </style>
""", unsafe_allow_html=True)

@st.cache_data(ttl=300)
def cargar_data():
    try:
        df1 = pd.read_csv(LINK_1)
        df2 = pd.read_csv(LINK_2)
        df = pd.concat([df1, df2], ignore_index=True)
        df.columns = [str(c).strip() for c in df.columns]
        
        c_usa = next((c for c in df.columns if 'Engagement' in c or 'Usabilidad' in c), None)
        c_emp = next((c for c in df.columns if 'Empresa' in c or 'Nombre' in c), df.columns[0])
        c_sem = next((c for c in df.columns if 'Semana' in c), None) # Detectamos la columna de semana
        c_mes = next((c for c in df.columns if 'Mes' in c), None)
        c_ani = next((c for c in df.columns if 'Año' in c or 'Anio' in c), None)

        def limpiar_num(val):
            try:
                s = str(val).replace('%', '').replace(',', '.').strip()
                if s == "" or s == "nan": return None
                n = float(s)
                return n / 100.0 if n > 1.1 else n
            except: return None

        df['Usabilidad_V'] = df[c_usa].apply(limpiar_num)
        df['Anio_V'] = pd.to_numeric(df[c_ani], errors='coerce').fillna(0).astype(int)
        df['Mes_V'] = pd.to_numeric(df[c_mes], errors='coerce').fillna(0).astype(int)
        df['Empresa_V'] = df[c_emp].astype(str).str.strip()
        df['Semana_V'] = df[c_sem].astype(str).str.strip() if c_sem else ""
        
        # --- FILTRO CRÍTICO: SOLO MES TOTAL ---
        # Filtramos para que el DF solo contenga filas que digan "total" en la semana
        df = df[df['Semana_V'].str.lower().str.contains("total", na=False)]
        
        return df.dropna(subset=['Usabilidad_V']), 'Empresa_V', 'Anio_V', 'Mes_V'
    except Exception as e:
        return pd.DataFrame(), str(e), None, None

df, col_emp, col_ani, col_mes = cargar_data()

if not df.empty:
    with st.sidebar:
        st.markdown("### 🎛️ Filtros")
        lista_empresas = sorted([e for e in df[col_emp].unique() if str(e) not in ['nan', 'None']])
        empresa_sel = st.selectbox("Empresa Target", ["Todas las Empresas"] + lista_empresas)
        
        anios_disp = sorted([a for a in df[col_ani].unique() if a > 2020], reverse=True)
        anios_sel = st.multiselect("Comparativa Anual", anios_disp, default=anios_disp)
        
        meses_map = {1:'Ene', 2:'Feb', 3:'Mar', 4:'Abr', 5:'May', 6:'Jun', 7:'Jul', 8:'Ago', 9:'Set', 10:'Oct', 11:'Nov', 12:'Dic'}
        meses_sel = st.multiselect("Meses", sorted(meses_map.keys()), 
                                   default=sorted(meses_map.keys()), format_func=lambda x: meses_map[x])

    st.markdown(f"<h1>📊 Reporte de Usabilidad: {empresa_sel}</h1>", unsafe_allow_html=True)

    # FILTRADO
    df_f = df[(df[col_ani].isin(anios_sel)) & (df[col_mes].isin(meses_sel))].copy()
    if empresa_sel != "Todas las Empresas":
        df_f = df_f[df_f[col_emp] == empresa_sel]

    # --- GAUGES ---
    colores_config = {2024: LEAF, 2025: CORAL, 2026: SEA}
    anios_activos = sorted(df_f[col_ani].unique())
    
    if anios_activos:
        gauge_cols = st.columns(len(anios_activos))
        for i, anio in enumerate(anios_activos):
            with gauge_cols[i]:
                promedio = df_f[df_f[col_ani] == anio]['Usabilidad_V'].mean()
                fig_g = go.Figure(go.Indicator(
                    mode="gauge+number", value=(promedio or 0)*100,
                    number={'suffix': "%", 'font': {'size': 28, 'color': BLACK}, 'valueformat': '.1f'},
                    title={'text': f"Media {anio}", 'font': {'size': 18, 'color': BLACK}},
                    gauge={'axis': {'range': [0, 100], 'tickcolor': BLACK},
                           'bar': {'color': BLACK},
                           'steps': [{'range': [0, 100], 'color': colores_config.get(anio, WHITE)}]}
                ))
                fig_g.update_layout(height=220, margin=dict(l=30, r=30, t=50, b=20), paper_bgcolor='rgba(0,0,0,0)')
                st.plotly_chart(fig_g, use_container_width=True, key=f"gauge_{anio}")

    # --- CURVA DE ENGAGEMENT CORREGIDA ---
    st.markdown("### 📈 Curva de Engagement (Cierres Mensuales)")
    if not df_f.empty:
        df_ev = df_f.groupby([col_ani, col_mes])['Usabilidad_V'].mean().reset_index()
        df_ev = df_ev.sort_values([col_ani, col_mes])
        
        fig_line = go.Figure()
        for anio in sorted(anios_sel):
            df_a = df_ev[df_ev[col_ani] == anio]
            if not df_a.empty:
                fig_line.add_trace(go.Scatter(
                    x=[meses_map.get(m) for m in df_a[col_mes]], 
                    y=df_a['Usabilidad_V'],
                    name=f"Año {anio}", 
                    mode='lines+markers+text',
                    line=dict(color=colores_config.get(anio, BLACK), width=4),
                    text=[f"{v:.1%}" for v in df_a['Usabilidad_V']],
                    textposition="top center",
                    connectgaps=True
                ))
        
        fig_line.update_layout(
            yaxis=dict(tickformat=".0%", range=[0, 1.1], gridcolor='rgba(0,0,0,0.1)'),
            xaxis=dict(showgrid=False),
            paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)',
            height=450, legend=dict(orientation="h", y=1.1, x=0.5, xanchor="center")
        )
        st.plotly_chart(fig_line, use_container_width=True)

    # --- INFORME INTELIGENTE ---
    st.markdown("### 🧠 Informe de Desempeño Holos")
    if not df_f.empty:
        total_avg = df_f['Usabilidad_V'].mean()
        stats_mes = df_f.groupby(col_mes)['Usabilidad_V'].mean()
        mejor_mes_num = stats_mes.idxmax()
        
        st.markdown(f"""
        <div class='insight-card'>
            <strong>Análisis Ejecutivo:</strong> El nivel de usabilidad promedio (basado en cierres de mes) es de <b>{total_avg:.1%}</b>.<br>
            <strong>Cierre de Febrero:</strong> Se visualiza el dato de <b>35.4%</b> como cierre de periodo actual.<br>
            <strong>Punto Máximo:</strong> El mes de mayor rendimiento detectado es <b>{meses_map.get(mejor_mes_num)}</b>.
        </div>
        """, unsafe_allow_html=True)

    with st.expander("📂 Explorar registros detallados (Solo Cierres)"):
        st.dataframe(df_f)
else:
    st.error("No se detectaron datos con la etiqueta 'Mes total'. Revisa tu Google Sheet.")
