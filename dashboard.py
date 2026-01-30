import streamlit as st
import pandas as pd
import plotly.graph_objects as go
import plotly.express as px

# 1. Configuración de pantalla completa y título de pestaña
st.set_page_config(page_title="Executive Insights | Beholos", layout="wide", initial_sidebar_state="expanded")

# --- LINKS DE DATA ---
LINK_1 = "https://docs.google.com/spreadsheets/d/e/2PACX-1vSWiXR7BLxwzX2wtD_uF59pvxtus8BL5iqgymKSh2-Llwt6smOJzR7ROUxICr57DA/pub?gid=1638907402&single=true&output=csv"
LINK_2 = "https://docs.google.com/spreadsheets/d/e/2PACX-1vSWiXR7BLxwzX2wtD_uF59pvxtus8BL5iqgymKSh2-Llwt6smOJzR7ROUxICr57DA/pub?gid=1341962834&single=true&output=csv"

# --- DISEÑO UI PREMIUM (CSS) ---
st.markdown("""
    <style>
        @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;700&display=swap');
        html, body, [class*="css"] { font-family: 'Inter', sans-serif; }
        .stApp { background-color: #F8FAFC; }
        .main-title { color: #1E293B; font-size: 36px; font-weight: 700; margin-bottom: 20px; }
        .card { background-color: white; padding: 20px; border-radius: 15px; box-shadow: 0 4px 6px -1px rgb(0 0 0 / 0.1); margin-bottom: 20px; }
        .insight-box { background-color: #EFF6FF; border-left: 5px solid #3B82F6; padding: 15px; border-radius: 5px; }
    </style>
""", unsafe_allow_html=True)

@st.cache_data(ttl=300)
def load_and_clean():
    try:
        df1 = pd.read_csv(LINK_1)
        df2 = pd.read_csv(LINK_2)
        df = pd.concat([df1, df2], ignore_index=True)
        df.columns = [str(c).strip() for c in df.columns]
        
        # Mapeo de columnas dinámico
        c_emp = next((c for c in df.columns if 'Empresa' in c or 'Nombre' in c), df.columns[0])
        c_usa = next((c for c in df.columns if 'Engagement' in c or 'Usabilidad' in c), None)
        c_ani = next((c for c in df.columns if 'Año' in c or 'Anio' in c), None)
        c_mes = next((c for c in df.columns if 'Mes' in c), None)

        # Limpieza profunda
        df['Val_Usa'] = pd.to_numeric(df[c_usa].astype(str).str.replace('%', '').str.replace(',', '.'), errors='coerce').fillna(0)
        if df['Val_Usa'].max() > 1.1: df['Val_Usa'] = df['Val_Usa'] / 100
        
        df['Anio_Limpio'] = pd.to_numeric(df[c_ani], errors='coerce').fillna(0).astype(int)
        df['Mes_Limpio'] = pd.to_numeric(df[c_mes], errors='coerce').fillna(0).astype(int)
        
        return df, c_emp, 'Anio_Limpio', 'Mes_Limpio'
    except Exception as e:
        st.error(f"Error de conexión: {e}")
        return pd.DataFrame(), None, None, None

df, col_emp, col_ani, col_mes = load_and_clean()

if not df.empty:
    # --- SIDEBAR (FILTROS) ---
    with st.sidebar:
        st.image("https://cdn-icons-png.flaticon.com/512/1087/1087113.png", width=80) # Icono decorativo
        st.header("Panel de Control")
        
        emp_list = sorted([e for e in df[col_emp].unique() if str(e) != 'nan'])
        emp_sel = st.selectbox("Seleccionar Empresa", ["Todas las Empresas"] + emp_list)
        
        anios_disp = sorted([a for a in df[col_ani].unique() if a > 2000], reverse=True)
        anios_sel = st.multiselect("Años Fiscales", anios_disp, default=anios_disp)
        
        meses_map = {1:'Enero', 2:'Febrero', 3:'Marzo', 4:'Abril', 5:'Mayo', 6:'Junio', 
                     7:'Julio', 8:'Agosto', 9:'Septiembre', 10:'Octubre', 11:'Noviembre', 12:'Diciembre'}
        meses_sel = st.multiselect("Filtro Mensual", sorted(meses_map.keys()), 
                                   default=sorted(meses_map.keys()), format_func=lambda x: meses_map[x])

    # Filtrado Final
    df_f = df[(df[col_ani].isin(anios_sel)) & (df[col_mes].isin(meses_sel))].copy()
    if emp_sel != "Todas las Empresas":
        df_f = df_f[df_f[col_emp] == emp_sel]

    # --- ENCABEZADO ---
    st.markdown(f"<div class='main-title'>📊 Reporte de Usabilidad: {emp_sel}</div>", unsafe_allow_html=True)

    # --- INDICADORES (GAUGES) ---
    colores = {2024: "#FDE047", 2025: "#FB923C", 2026: "#93C5FD"} # Amarillo, Naranja, Azul claro
    
    anios_activos = sorted(df_f[col_ani].unique())
    if anios_activos:
        cols = st.columns(len(anios_activos))
        for i, a in enumerate(anios_activos):
            with cols[i]:
                val = df_f[df_f[col_ani] == a]['Val_Usa'].mean()
                fig = go.Figure(go.Indicator(
                    mode="gauge+number", value=val*100,
                    number={'suffix': "%", 'font': {'size': 32, 'color': '#1E293B'}, 'valueformat': '.1f'},
                    title={'text': f"KPI {a}", 'font': {'size': 18, 'color': '#64748B'}},
                    gauge={
                        'axis': {'range': [0, 100], 'tickwidth': 1},
                        'bar': {'color': "#1E293B"},
                        'bgcolor': "white",
                        'steps': [{'range': [0, 100], 'color': colores.get(a, "#E2E8F0")}],
                        'threshold': {'line': {'color': "red", 'width': 4}, 'thickness': 0.75, 'value': 90}
                    }
                ))
                fig.update_layout(height=250, margin=dict(l=30, r=30, t=50, b=20), paper_bgcolor='rgba(0,0,0,0)')
                st.plotly_chart(fig, use_container_width=True)

    # --- CUERPO PRINCIPAL (GRÁFICA + INFORME) ---
    c_graf, c_info = st.columns([2, 1])

    with c_graf:
        st.markdown("### 📈 Evolución Estratégica")
        df_ev = df_f.groupby([col_mes, col_ani])['Val_Usa'].mean().reset_index()
        fig_line = go.Figure()
        
        for a in sorted(anios_sel):
            df_a = df_ev[df_ev[col_ani] == a].sort_values(col_mes)
            if not df_a.empty:
                fig_line.add_trace(go.Scatter(
                    x=[meses_map.get(m, m) for m in df_a[col_mes]], 
                    y=df_a['Val_Usa'],
                    name=f"Ciclo {a}", mode='lines+markers',
                    line=dict(color=colores.get(a), width=4),
                    marker=dict(size=8, borderwidth=2)
                ))

        fig_line.update_layout(
            yaxis=dict(tickformat=".0%", range=[0, 1.05], gridcolor='#E2E8F0'),
            xaxis=dict(gridcolor='#E2E8F0'),
            paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)',
            height=450, legend=dict(orientation="h", y=1.1, x=0.5, xanchor="center")
        )
        st.plotly_chart(fig_line, use_container_width=True)

    with c_info:
        st.markdown("### 🧠 Informe Inteligente")
        if not df_f.empty:
            avg_actual = df_f['Val_Usa'].mean()
            max_mes = df_f.groupby(col_mes)['Val_Usa'].mean().idxmax()
            
            # Lógica de análisis
            estado = "Óptimo" if avg_actual > 0.8 else "Estable" if avg_actual > 0.4 else "Crítico"
            color_text = "green" if estado == "Óptimo" else "orange" if estado == "Estable" else "red"

            st.markdown(f"""
            <div class='insight-box'>
                <strong>Resumen Ejecutivo:</strong><br>
                La usabilidad general se encuentra en un estado <span style='color:{color_text}; font-weight:bold'>{estado}</span> con un promedio de <b>{avg_actual:.1%}</b>.<br><br>
                <strong>Hito Detectado:</strong><br>
                El mes de mayor rendimiento histórico es <b>{meses_map.get(max_mes)}</b>. 
                Se recomienda replicar las estrategias de dicho periodo.
            </div>
            """, unsafe_allow_html=True)
            
            st.info(f"💡 Se están analizando {len(df_f)} registros de la base de datos consolidada.")

    # --- TABLA DETALLADA ---
    with st.expander("📂 Explorar registros de auditoría"):
        st.dataframe(df_f.style.format({c_usa: '{:.1%}'}), use_container_width=True)

else:
    st.error("⚠️ No se pudieron cargar los datos. Verifica que el archivo de Google Sheets sea público.")
