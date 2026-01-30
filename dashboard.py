import streamlit as st
import pandas as pd
import plotly.graph_objects as go

# 1. Configuración de pantalla
st.set_page_config(page_title="Holos | Business Intelligence", layout="wide")

# --- ENLACES REALES (CSV directo para evitar Error 404) ---
LINK_1 = "https://docs.google.com/spreadsheets/d/e/2PACX-1vSWiXR7BLxwzX2wtD_uF59pvxtus8BL5iqgymKSh2-Llwt6smOJzR7ROUxICr57DA/pub?gid=1638907402&single=true&output=csv"
LINK_2 = "https://docs.google.com/spreadsheets/d/e/2PACX-1vSWiXR7BLxwzX2wtD_uF59pvxtus8BL5iqgymKSh2-Llwt6smOJzR7ROUxICr57DA/pub?gid=1341962834&single=true&output=csv"

# --- IDENTIDAD VISUAL HOLOS ---
AZUL_HOLOS = "#1E293B"
AMARILLO_HOLOS = "#FACC15"
CORAL_HOLOS = "#FB923C"
CELESTE_FONDO = "#D1E9F6"

# --- ESTILO CSS PREMIUM ---
st.markdown(f"""
    <link href="https://fonts.googleapis.com/css2?family=Philosopher:wght@700&family=Inter:wght@400;600&display=swap" rel="stylesheet">
    <style>
        .stApp {{ background-color: {CELESTE_FONDO}; }}
        h1, h2, h3 {{ font-family: 'Philosopher', sans-serif !important; color: {AZUL_HOLOS}; }}
        * {{ font-family: 'Inter', sans-serif; }}
        .stMetric {{ background-color: white; padding: 15px; border-radius: 10px; box-shadow: 0 2px 4px rgba(0,0,0,0.05); }}
        [data-testid="stSidebar"] {{ background-color: #FFFFFF; }}
        .insight-box {{ background-color: white; border-left: 5px solid {AMARILLO_HOLOS}; padding: 15px; border-radius: 5px; }}
    </style>
""", unsafe_allow_html=True)

@st.cache_data(ttl=300)
def cargar_datos_seguros():
    try:
        # Cargamos directamente los links de publicación web para evitar errores de conexión
        df1 = pd.read_csv(LINK_1)
        df2 = pd.read_csv(LINK_2)
        df = pd.concat([df1, df2], ignore_index=True)
        
        df.columns = [str(c).strip() for c in df.columns]
        
        # Buscador de columnas inteligente
        c_usa = next((c for c in df.columns if 'Engagement' in c or 'Usabilidad' in c), None)
        c_emp = next((c for c in df.columns if 'Empresa' in c or 'Nombre' in c), df.columns[0])
        c_mes = next((c for c in df.columns if 'Mes' in c), None)
        c_ani = next((c for c in df.columns if 'Año' in c or 'Anio' in c), None)

        def limpiar_valor(val):
            try:
                s = str(val).replace('%', '').replace(',', '.').strip()
                n = float(s)
                return n / 100.0 if n > 1.1 else n
            except: return 0.0

        df['Val_Usa'] = df[c_usa].apply(limpiar_valor)
        df['Anio_L'] = pd.to_numeric(df[c_ani], errors='coerce').fillna(0).astype(int)
        df['Mes_L'] = pd.to_numeric(df[c_mes], errors='coerce').fillna(0).astype(int)
        df['Empresa_L'] = df[c_emp].astype(str).str.strip()
        
        return df, 'Empresa_L', 'Anio_L', 'Mes_L'
    except Exception as e:
        return pd.DataFrame(), str(e), None, None

df, col_emp, col_ani, col_mes = cargar_datos_seguros()

if not df.empty:
    # --- SIDEBAR ---
    with st.sidebar:
        st.header("🎛️ Filtros")
        empresas = sorted([e for e in df[col_emp].unique() if str(e) not in ['nan', 'None']])
        emp_sel = st.selectbox("Selecciona Empresa", ["Todas las Empresas"] + empresas)
        
        anios_disp = sorted([a for a in df[col_ani].unique() if a > 2020], reverse=True)
        anios_sel = st.multiselect("Años a mostrar", anios_disp, default=anios_disp)
        
        meses_map = {1:'Ene', 2:'Feb', 3:'Mar', 4:'Abr', 5:'May', 6:'Jun', 7:'Jul', 8:'Ago', 9:'Set', 10:'Oct', 11:'Nov', 12:'Dic'}
        meses_sel = st.multiselect("Filtrar Meses", sorted(meses_map.keys()), 
                                   default=sorted(meses_map.keys()), format_func=lambda x: meses_map[x])

    st.markdown(f"<h1>Reporte de Usabilidad: {emp_sel}</h1>", unsafe_allow_html=True)

    # Filtrado
    df_f = df[(df[col_ani].isin(anios_sel)) & (df[col_mes].isin(meses_sel))].copy()
    if emp_sel != "Todas las Empresas":
        df_f = df_f[df_f[col_emp] == emp_sel]

    # --- GAUGES ---
    colores_anios = {2024: CORAL_HOLOS, 2025: AMARILLO_HOLOS, 2026: AZUL_HOLOS}
    
    anios_activos = sorted(df_f[col_ani].unique())
    if anios_activos:
        cols = st.columns(len(anios_activos))
        for i, a in enumerate(anios_activos):
            with cols[i]:
                val_anio = df_f[df_f[col_ani] == a]['Val_Usa'].mean()
                fig_g = go.Figure(go.Indicator(
                    mode="gauge+number", value=val_anio*100,
                    number={'suffix': "%", 'font': {'size': 26, 'color': AZUL_HOLOS}},
                    title={'text': f"Promedio {a}", 'font': {'size': 18}},
                    gauge={'axis': {'range': [0, 100]}, 'bar': {'color': AZUL_HOLOS},
                           'steps': [{'range': [0, 100], 'color': colores_anios.get(a, "#EEE")}]}
                ))
                fig_g.update_layout(height=180, margin=dict(l=20, r=20, t=40, b=10), paper_bgcolor='rgba(0,0,0,0)')
                st.plotly_chart(fig_g, use_container_width=True, key=f"g_{a}")

    # --- GRÁFICA DE EVOLUCIÓN ---
    st.markdown("### 📈 Curva de Engagement")
    if not df_f.empty:
        df_ev = df_f.groupby([col_mes, col_ani])['Val_Usa'].mean().reset_index()
        fig_line = go.Figure()
        
        for a in sorted(anios_sel):
            df_a = df_ev[df_ev[col_ani] == a].sort_values(col_mes)
            if not df_a.empty:
                nombres_meses = [meses_map.get(m, str(m)) for m in df_a[col_mes]]
                fig_line.add_trace(go.Scatter(
                    x=nombres_meses, y=df_a['Val_Usa'],
                    name=f"Año {a}", mode='lines+markers+text',
                    line=dict(color=colores_anios.get(a, AZUL_HOLOS), width=4),
                    text=[f"{v:.1%}" for v in df_a['Val_Usa']],
                    textposition="top center"
                ))
        
        fig_line.update_layout(
            yaxis=dict(tickformat=".0%", range=[0, 1.1], gridcolor='rgba(0,0,0,0.1)'),
            paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)',
            height=400, legend=dict(orientation="h", y=1.1, x=0.5, xanchor="center")
        )
        st.plotly_chart(fig_line, use_container_width=True)

    # --- INFORME INTELIGENTE ---
    st.markdown("### 🧠 Informe de Desempeño Holos")
    if not df_f.empty:
        avg_total = df_f['Val_Usa'].mean()
        mejor_mes_idx = df_f.groupby(col_mes)['Val_Usa'].mean().idxmax()
        
        st.markdown(f"""
        <div class='insight-box'>
            <strong>Resumen Ejecutivo:</strong> La usabilidad consolidada es de <b>{avg_total:.1%}</b>.<br>
            <strong>Hito Detectado:</strong> El mes con mayor engagement bajo estos filtros es <b>{meses_map.get(mejor_mes_idx)}</b>.<br>
            <strong>Sugerencia:</strong> Mantener el monitoreo en los canales de atención para sostener la curva del {max(anios_sel)}.
        </div>
        """, unsafe_allow_html=True)

    with st.expander("📂 Ver registros detallados"):
        st.dataframe(df_f)
else:
    st.error(f"Error al cargar datos: {col_emp}")
