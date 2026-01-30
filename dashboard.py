import streamlit as st
import pandas as pd
import plotly.graph_objects as go

# 1. Configuración de pantalla
st.set_page_config(page_title="Holos | Dashboard de Usabilidad", layout="wide")

# --- LINKS DE DATA ---
LINK_1 = "https://docs.google.com/spreadsheets/d/e/2PACX-1vSWiXR7BLxwzX2wtD_uF59pvxtus8BL5iqgymKSh2-Llwt6smOJzR7ROUxICr57DA/pub?gid=1638907402&single=true&output=csv"
LINK_2 = "https://docs.google.com/spreadsheets/d/e/2PACX-1vSWiXR7BLxwzX2wtD_uF59pvxtus8BL5iqgymKSh2-Llwt6smOJzR7ROUxICr57DA/pub?gid=1341962834&single=true&output=csv"

# --- PALETA DE COLORES HOLOS ---
AZUL_HOLOS = "#1E293B"  # Azul Oscuro Profesional
AMARILLO_HOLOS = "#FACC15" # Amarillo Vibrante
GRIS_SUAVE = "#F8FAFC"
CORAL_HOLOS = "#FB923C" # Para destacar años previos

# --- UI CUSTOMIZATION ---
st.markdown(f"""
    <style>
        .stApp {{ background-color: {GRIS_SUAVE}; }}
        .main-header {{ color: {AZUL_HOLOS}; font-size: 32px; font-weight: 800; border-bottom: 3px solid {AMARILLO_HOLOS}; padding-bottom: 10px; margin-bottom: 25px; }}
        .metric-card {{ background: white; padding: 20px; border-radius: 12px; box-shadow: 0 4px 6px rgba(0,0,0,0.05); text-align: center; }}
        .insight-box {{ background-color: white; border-top: 5px solid {AMARILLO_HOLOS}; padding: 20px; border-radius: 10px; box-shadow: 0 4px 10px rgba(0,0,0,0.05); }}
    </style>
""", unsafe_allow_html=True)

@st.cache_data(ttl=300)
def get_data():
    try:
        df1 = pd.read_csv(LINK_1)
        df2 = pd.read_csv(LINK_2)
        df = pd.concat([df1, df2], ignore_index=True)
        df.columns = [str(c).strip() for c in df.columns]
        
        c_emp = next((c for c in df.columns if 'Empresa' in c or 'Nombre' in c), df.columns[0])
        c_usa = next((c for c in df.columns if 'Engagement' in c or 'Usabilidad' in c), None)
        c_ani = next((c for c in df.columns if 'Año' in c or 'Anio' in c), None)
        c_mes = next((c for c in df.columns if 'Mes' in c), None)

        df['Val_Usa'] = pd.to_numeric(df[c_usa].astype(str).str.replace('%', '').str.replace(',', '.'), errors='coerce').fillna(0)
        if df['Val_Usa'].max() > 1.1: df['Val_Usa'] = df['Val_Usa'] / 100
        
        df['Anio_L'] = pd.to_numeric(df[c_ani], errors='coerce').fillna(0).astype(int)
        df['Mes_L'] = pd.to_numeric(df[c_mes], errors='coerce').fillna(0).astype(int)
        
        return df, c_emp, 'Anio_L', 'Mes_L'
    except Exception as e:
        st.error(f"Error de conexión: {e}")
        return pd.DataFrame(), None, None, None

df, col_emp, col_ani, col_mes = get_data()

if not df.empty:
    # --- FILTROS (SIDEBAR) ---
    with st.sidebar:
        st.markdown("### 🛠️ Configuración")
        emp_list = sorted([e for e in df[col_emp].unique() if str(e) != 'nan'])
        emp_sel = st.selectbox("Empresa", ["Todas las Empresas"] + emp_list)
        
        anios_disp = sorted([a for a in df[col_ani].unique() if a > 2000], reverse=True)
        anios_sel = st.multiselect("Años", anios_disp, default=anios_disp)
        
        meses_map = {1:'Enero', 2:'Febrero', 3:'Marzo', 4:'Abril', 5:'Mayo', 6:'Junio', 
                     7:'Julio', 8:'Agosto', 9:'Septiembre', 10:'Octubre', 11:'Noviembre', 12:'Diciembre'}
        meses_sel = st.multiselect("Meses", sorted(meses_map.keys()), 
                                   default=sorted(meses_map.keys()), format_func=lambda x: meses_map[x])

    # Filtrar
    df_f = df[(df[col_ani].isin(anios_sel)) & (df[col_mes].isin(meses_sel))].copy()
    if emp_sel != "Todas las Empresas":
        df_f = df_f[df_f[col_emp] == emp_sel]

    st.markdown(f"<div class='main-header'>Dashboard de Usabilidad | {emp_sel}</div>", unsafe_allow_html=True)

    # --- KPI GAUGES ---
    # Asignamos colores de la marca a los años
    color_map = {2024: CORAL_HOLOS, 2025: AMARILLO_HOLOS, 2026: AZUL_HOLOS}
    
    anios_activos = sorted(df_f[col_ani].unique())
    if anios_activos:
        cols = st.columns(len(anios_activos))
        for i, a in enumerate(anios_activos):
            with cols[i]:
                val = df_f[df_f[col_ani] == a]['Val_Usa'].mean()
                fig = go.Figure(go.Indicator(
                    mode="gauge+number", value=val*100,
                    number={'suffix': "%", 'font': {'color': AZUL_HOLOS, 'size': 35}, 'valueformat': '.1f'},
                    title={'text': f"Meta {a}", 'font': {'color': '#64748B', 'size': 16}},
                    gauge={
                        'axis': {'range': [0, 100], 'tickcolor': AZUL_HOLOS},
                        'bar': {'color': AZUL_HOLOS},
                        'bgcolor': "white",
                        'steps': [{'range': [0, 100], 'color': "#F1F5F9"}],
                        'threshold': {'line': {'color': color_map.get(a, AMARILLO_HOLOS), 'width': 8}, 'thickness': 0.8, 'value': val*100}
                    }
                ))
                fig.update_layout(height=240, margin=dict(l=20, r=20, t=40, b=20), paper_bgcolor='rgba(0,0,0,0)')
                st.plotly_chart(fig, use_container_width=True)

    # --- GRÁFICA Y REPORTE ---
    col_g, col_i = st.columns([2, 1])

    with col_g:
        st.markdown("### 📉 Curva de Engagement")
        df_ev = df_f.groupby([col_mes, col_ani])['Val_Usa'].mean().reset_index()
        fig_line = go.Figure()
        
        for a in sorted(anios_sel):
            df_a = df_ev[df_ev[col_ani] == a].sort_values(col_mes)
            if not df_a.empty:
                fig_line.add_trace(go.Scatter(
                    x=[meses_map.get(m) for m in df_a[col_mes]], y=df_a['Val_Usa'],
                    name=f"Año {a}", mode='lines+markers',
                    line=dict(color=color_map.get(a, AZUL_HOLOS), width=4),
                    marker=dict(size=10, bordercolor="white", borderwidth=2)
                ))
        fig_line.update_layout(
            yaxis=dict(tickformat=".0%", range=[0, 1.05], gridcolor='#E2E8F0'),
            paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)',
            height=400, legend=dict(orientation="h", y=1.1, x=0.5, xanchor="center")
        )
        st.plotly_chart(fig_line, use_container_width=True)

    with col_i:
        st.markdown("### 📖 Informe Inteligente")
        avg_total = df_f['Val_Usa'].mean()
        mejor_mes_idx = df_f.groupby(col_mes)['Val_Usa'].mean().idxmax() if not df_f.empty else 1
        
        st.markdown(f"""
        <div class='insight-box'>
            <p style='color: {AZUL_HOLOS}; font-size: 1.1rem;'>
            <b>Resumen Global:</b> El promedio consolidado es del <b>{avg_total:.1%}</b>.
            </p>
            <hr>
            <p>🌟 <b>Punto Máximo:</b> Se observa el mayor rendimiento en el mes de <b>{meses_map.get(mejor_mes_idx)}</b>.</p>
            <p>💡 <b>Insight:</b> La tendencia muestra que los años más recientes han tenido un ajuste en la consistencia de datos.</p>
        </div>
        """, unsafe_allow_html=True)

    # --- DATA EXPLORER ---
    with st.expander("🔍 Explorar Datos Crudos"):
        st.dataframe(df_f, use_container_width=True)

else:
    st.error("Hubo un problema al cargar los datos desde Google Sheets.")
