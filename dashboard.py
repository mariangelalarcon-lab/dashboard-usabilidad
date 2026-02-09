import streamlit as st
import pandas as pd
import plotly.graph_objects as go

# 1. Configuración de pantalla
st.set_page_config(page_title="Holos | Business Intelligence", layout="wide")

# --- ENLACES DE DATOS DIRECTOS ---
LINK_1 = "https://docs.google.com/spreadsheets/d/e/2PACX-1vSWiXR7BLxwzX2wtD_uF59pvxtus8BL5iqgymKSh2-Llwt6smOJzR7ROUxICr57DA/pub?gid=1638907402&single=true&output=csv"
LINK_2 = "https://docs.google.com/spreadsheets/d/e/2PACX-1vSWiXR7BLxwzX2wtD_uF59pvxtus8BL5iqgymKSh2-Llwt6smOJzR7ROUxICr57DA/pub?gid=1341962834&single=true&output=csv"

# --- PALETA OFICIAL HOLOS ---
SKY, LEAF, SEA, CORAL, BLACK, WHITE = "#D1E9F6", "#F1FB8C", "#A9C1F5", "#FF9F86", "#000000", "#FFFFFF"

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

@st.cache_data(ttl=60) # Reducido a 60 seg para ver cambios del Excel rápido
def cargar_data():
    try:
        df1 = pd.read_csv(LINK_1)
        df2 = pd.read_csv(LINK_2)
        df = pd.concat([df1, df2], ignore_index=True)
        df.columns = [str(c).strip() for c in df.columns]
        
        # Mapeo inteligente de columnas
        c_usa = next((c for c in df.columns if 'Engagement' in c or 'Usabilidad' in c), df.columns[7])
        c_emp = next((c for c in df.columns if 'Empresa' in c or 'Nombre' in c), df.columns[0])
        c_sem = next((c for c in df.columns if 'Semana' in c), df.columns[1])
        c_mes = next((c for c in df.columns if 'Mes' in c and 'inicio' not in c.lower()), df.columns[8])
        c_ani = next((c for c in df.columns if 'Año' in c or 'Anio' in c), df.columns[11])

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
        df['Semana_V'] = df[c_sem].astype(str).str.strip()
        
        return df, 'Empresa_V', 'Anio_V', 'Mes_V', 'Semana_V'
    except Exception as e:
        return pd.DataFrame(), str(e), None, None, None

df, col_emp, col_ani, col_mes, col_sem = cargar_data()

if not df.empty:
    with st.sidebar:
        st.markdown("### 🎛️ Filtros")
        
        # --- NUEVO SELECTOR DE VISTA ---
        tipo_vista = st.radio("Nivel de Análisis:", ["Ejecutivo (Cierres)", "Operativo (Semanal)"])
        
        lista_empresas = sorted([e for e in df[col_emp].unique() if str(e) not in ['nan', 'None']])
        empresa_sel = st.selectbox("Empresa Target", ["Todas las Empresas"] + lista_empresas)
        
        anios_disp = sorted([a for a in df[col_ani].unique() if a > 2020], reverse=True)
        anios_sel = st.multiselect("Años", anios_disp, default=[2025, 2026])
        
        meses_map = {1:'Ene', 2:'Feb', 3:'Mar', 4:'Abr', 5:'May', 6:'Jun', 7:'Jul', 8:'Ago', 9:'Set', 10:'Oct', 11:'Nov', 12:'Dic'}
        meses_sel = st.multiselect("Meses", sorted(meses_map.keys()), 
                                   default=list(meses_map.keys()), format_func=lambda x: meses_map[x])

    st.markdown(f"<h1>📊 Reporte de Usabilidad: {empresa_sel}</h1>", unsafe_allow_html=True)

    # --- FILTRADO POR MODO ---
    df_f = df[(df[col_ani].isin(anios_sel)) & (df[col_mes].isin(meses_sel))].copy()
    
    if empresa_sel != "Todas las Empresas":
        df_f = df_f[df_f[col_emp] == empresa_sel]

    # Aplicamos el filtro de Cierres vs Semanal
    if tipo_vista == "Ejecutivo (Cierres)":
        df_vis = df_f[df_f[col_sem].str.contains('total|Total', na=False)]
    else:
        # Modo Operativo: muestra las semanas de avance
        df_vis = df_f.copy()

    # --- GAUGES ---
    colores_config = {2024: LEAF, 2025: CORAL, 2026: SEA}
    anios_activos = sorted(df_vis[col_ani].unique())
    
    if anios_activos:
        gauge_cols = st.columns(len(anios_activos))
        for i, anio in enumerate(anios_activos):
            with gauge_cols[i]:
                promedio = df_vis[df_vis[col_ani] == anio]['Usabilidad_V'].mean()
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

    # --- CURVA DE ENGAGEMENT CON PROGRESO SEMANAL ---
    st.markdown(f"### 📈 Curva de Engagement ({tipo_vista})")
    if not df_vis.empty:
        # Agrupamos por Año, Mes y Semana para evitar cruces
        df_ev = df_vis.groupby([col_ani, col_mes, col_sem])['Usabilidad_V'].mean().reset_index()
        df_ev = df_ev.sort_values([col_ani, col_mes, col_sem]) 
        
        fig_line = go.Figure()
        for anio in anios_activos:
            df_a = df_ev[df_ev[col_ani] == anio]
            if not df_a.empty:
                # MODIFICACIÓN SOLICITADA: Combinar Mes y Semana en el eje X
                x_labels = [f"{meses_map.get(m)}-{s}" for m, s in zip(df_a[col_mes], df_a[col_sem])]
                
                fig_line.add_trace(go.Scatter(
                    x=x_labels, 
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
    if not df_vis.empty:
        total_avg = df_vis['Usabilidad_V'].mean()
        mejor_mes_num = df_vis.groupby(col_mes)['Usabilidad_V'].mean().idxmax()
        
        st.markdown(f"""
        <div class='insight-card'>
            <strong>Análisis Ejecutivo:</strong> El nivel de usabilidad promedio es de <b>{total_avg:.1%}</b>.<br>
            <strong>Estatus:</strong> Se visualiza el progreso <b>{tipo_vista.lower()}</b>.<br>
            <strong>Insight:</strong> El rendimiento máximo de la selección se encuentra en <b>{meses_map.get(mejor_mes_num)}</b>.
        </div>
        """, unsafe_allow_html=True)

    with st.expander("📂 Explorar registros detallados"):
        st.dataframe(df_vis[[col_emp, col_ani, col_mes, col_sem, 'Usabilidad_V']])
else:
    st.error("No se detectaron datos. Revisa la conexión con Google Sheets.")
