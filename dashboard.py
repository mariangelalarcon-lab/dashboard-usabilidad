import streamlit as st
import pandas as pd
import plotly.graph_objects as go

# 1. Configuración de página
st.set_page_config(page_title="Holos | Business Intelligence", layout="wide")

# --- ENLACES DE DATOS DIRECTOS ---
LINK_1 = "https://docs.google.com/spreadsheets/d/e/2PACX-1vSWiXR7BLxwzX2wtD_uF59pvxtus8BL5iqgymKSh2-Llwt6smOJzR7ROUxICr57DA/pub?gid=1638907402&single=true&output=csv"
LINK_2 = "https://docs.google.com/spreadsheets/d/e/2PACX-1vSWiXR7BLxwzX2wtD_uF59pvxtus8BL5iqgymKSh2-Llwt6smOJzR7ROUxICr57DA/pub?gid=1341962834&single=true&output=csv"

# --- PALETA DE COLORES OFICIAL HOLOS ---
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
        .insight-card {{ background-color: {WHITE}; border-left: 6px solid {LEAF}; padding: 20px; border-radius: 10px; box-shadow: 0 4px 6px rgba(0,0,0,0.05); }}
    </style>
""", unsafe_allow_html=True)

@st.cache_data(ttl=300)
def cargar_limpiar_data():
    try:
        df1 = pd.read_csv(LINK_1)
        df2 = pd.read_csv(LINK_2)
        df = pd.concat([df1, df2], ignore_index=True)
        df.columns = [str(c).strip() for c in df.columns]
        
        # Identificación de columnas clave
        c_usa = next((c for c in df.columns if 'Engagement' in c or 'Usabilidad' in c), None)
        c_emp = next((c for c in df.columns if 'Empresa' in c or 'Nombre' in c), df.columns[0])
        c_mes = next((c for c in df.columns if 'Mes' in c), None)
        c_ani = next((c for c in df.columns if 'Año' in c or 'Anio' in c), None)

        def limpiar_num(val):
            try:
                s = str(val).replace('%', '').replace(',', '.').strip()
                n = float(s)
                return n / 100.0 if n > 1.1 else n
            except: return 0.0

        df['Usabilidad_V'] = df[c_usa].apply(limpiar_num)
        df['Anio_V'] = pd.to_numeric(df[c_ani], errors='coerce').fillna(0).astype(int)
        df['Mes_V'] = pd.to_numeric(df[c_mes], errors='coerce').fillna(0).astype(int)
        df['Empresa_V'] = df[c_emp].astype(str).str.strip()
        
        return df, 'Empresa_V', 'Anio_V', 'Mes_V'
    except Exception as e:
        return pd.DataFrame(), str(e), None, None

df, col_emp, col_ani, col_mes = cargar_limpiar_data()

if not df.empty:
    # --- PANEL DE FILTROS ---
    with st.sidebar:
        st.markdown("### 🎛️ Filtros")
        lista_empresas = sorted([e for e in df[col_emp].unique() if str(e) not in ['nan', 'None']])
        empresa_sel = st.selectbox("Empresa Target", ["Todas las Empresas"] + lista_empresas)
        
        anios_disp = sorted([a for a in df[col_ani].unique() if a > 2020], reverse=True)
        anios_sel = st.multiselect("Comparativa Anual", anios_disp, default=anios_disp)
        
        meses_map = {1:'Ene', 2:'Feb', 3:'Mar', 4:'Abr', 5:'May', 6:'Jun', 7:'Jul', 8:'Ago', 9:'Set', 10:'Oct', 11:'Nov', 12:'Dic'}
        meses_sel = st.multiselect("Meses", sorted(meses_map.keys()), 
                                   default=sorted(meses_map.keys()), format_func=lambda x: meses_map[x])

    st.markdown(f"<h1>Reporte de Usabilidad: {empresa_sel}</h1>", unsafe_allow_html=True)

    # Filtrado lógico
    df_f = df[(df[col_ani].isin(anios_sel)) & (df[col_mes].isin(meses_sel))].copy()
    if empresa_sel != "Todas las Empresas":
        df_f = df_f[df_f[col_emp] == empresa_sel]

    # --- INDICADORES (GAUGES) ---
    # Asignación de colores según tu imagen
    colores_config = {2024: LEAF, 2025: CORAL, 2026: SEA}
    
    anios_activos = sorted(df_f[col_ani].unique())
    if anios_activos:
        gauge_cols = st.columns(len(anios_activos))
        for i, anio in enumerate(anios_activos):
            with gauge_cols[i]:
                promedio = df_f[df_f[col_ani] == anio]['Usabilidad_V'].mean()
                fig_g = go.Figure(go.Indicator(
                    mode="gauge+number", value=promedio*100,
                    number={'suffix': "%", 'font': {'size': 28, 'color': BLACK}},
                    title={'text': f"Promedio {anio}", 'font': {'size': 18}},
                    gauge={'axis': {'range': [0, 100], 'tickcolor': BLACK},
                           'bar': {'color': BLACK}, # Aguja/Barra en negro para contraste
                           'steps': [{'range': [0, 100], 'color': colores_config.get(anio, WHITE)}]}
                ))
                fig_g.update_layout(height=200, margin=dict(l=20, r=20, t=40, b=10), paper_bgcolor='rgba(0,0,0,0)')
                st.plotly_chart(fig_g, use_container_width=True, key=f"gauge_{anio}")

    # --- CURVA DE ENGAGEMENT ---
    st.markdown("### 📈 Curva de Engagement")
    if not df_f.empty:
        df_ev = df_f.groupby([col_mes, col_ani])['Usabilidad_V'].mean().reset_index()
        fig_line = go.Figure()
        
        for anio in sorted(anios_sel):
            df_a = df_ev[df_ev[col_ani] == anio].sort_values(col_mes)
            if not df_a.empty:
                # El .get(m, str(m)) previene el ValueError si hay meses 0 o nulos
                nombres_eje_x = [meses_map.get(m, str(m)) for m in df_a[col_mes]]
                fig_line.add_trace(go.Scatter(
                    x=nombres_eje_x, y=df_a['Usabilidad_V'],
                    name=f"Año {anio}", mode='lines+markers+text',
                    line=dict(color=colores_config.get(anio, BLACK), width=4),
                    text=[f"{v:.1%}" for v in df_a['Usabilidad_V']],
                    textposition="top center"
                ))
        
        fig_line.update_layout(
            yaxis=dict(tickformat=".0%", range=[0, 1.1], gridcolor='rgba(0,0,0,0.1)'),
            xaxis=dict(showgrid=False),
            paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)',
            height=450, legend=dict(orientation="h", y=1.1, x=0.5, xanchor="center")
        )
        st.plotly_chart(fig_line, use_container_width=True)

    # --- INFORME INTELIGENTE HOLOS ---
    st.markdown("### 🧠 Insights de Estrategia")
    if not df_f.empty:
        total_avg = df_f['Usabilidad_V'].mean()
        mejor_mes_val = df_f.groupby(col_mes)['Usabilidad_V'].mean().idxmax()
        
        st.markdown(f"""
        <div class='insight-card'>
            <strong>Análisis Ejecutivo:</strong> El nivel de usabilidad promedio es de <b>{total_avg:.1%}</b>.<br>
            <strong>Punto Crítico:</strong> El rendimiento más alto se concentra en el mes de <b>{meses_map.get(mejor_mes_val, mejor_mes_val)}</b>.<br>
            <strong>Recomendación:</strong> Se observa una tendencia positiva en el ciclo {max(anios_sel)}. 
            Mantener la estrategia de comunicación actual para estabilizar la curva.
        </div>
        """, unsafe_allow_html=True)

    with st.expander("📂 Explorar Base de Datos"):
        st.dataframe(df_f)

else:
    st.error("No se pudieron cargar los datos. Verifica los enlaces de publicación.")
