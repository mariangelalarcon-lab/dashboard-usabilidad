import streamlit as st
import pandas as pd
import plotly.graph_objects as go
import os

# 1. Configuración de página de alta definición
st.set_page_config(page_title="Reporte de Usabilidad", layout="wide", initial_sidebar_state="expanded")

# --- ESTILO CSS AVANZADO (Fondo celeste y fuentes) ---
st.markdown("""
    <link href="https://fonts.googleapis.com/css2?family=Philosopher:wght@400;700&family=Inter:wght@300;400;600&display=swap" rel="stylesheet">
    <style>
        * { font-family: 'Inter', sans-serif; }
        h1 { font-family: 'Philosopher', sans-serif !important; color: #1E293B; font-size: 3.2rem !important; margin-bottom: 0px; }
        h3 { font-family: 'Philosopher', sans-serif !important; color: #1E293B; }
        .stApp { background-color: #D1E9F6; } /* Regresamos al fondo celeste solicitado originalmente */
        
        /* Sidebar Profesional */
        [data-testid="stSidebar"] { background-color: #FFFFFF; border-right: 1px solid #E2E8F0; }
        
        /* Contenedores de KPIs e Insights */
        .insight-card {
            background-color: rgba(255, 255, 255, 0.7); padding: 15px; border-radius: 12px;
            border: 1px solid rgba(255,255,255,0.5); margin-bottom: 10px;
        }
    </style>
""", unsafe_allow_html=True)

def encontrar_columna(df, palabras_clave):
    for col in df.columns:
        for palabra in palabras_clave:
            if palabra.lower() in col.lower(): return col
    return None

@st.cache_data
def load_data():
    archivos_csv = [f for f in os.listdir('.') if f.endswith('.csv')]
    if not archivos_csv: return pd.DataFrame()
    lista_df = [pd.read_csv(f) for f in archivos_csv]
    df = pd.concat(lista_df, ignore_index=True)
    
    c_emp = encontrar_columna(df, ['Nombre', 'Empresa'])
    c_usa = encontrar_columna(df, ['% Usabilidad', 'Engagement'])
    c_mes = encontrar_columna(df, ['Inicio del Mes', 'Mes'])
    c_ani = encontrar_columna(df, ['Inicio de Año', 'Año'])
    c_sem = encontrar_columna(df, ['Semana', 'Desglose']) 

    def limpiar_pct(row):
        valor = row[c_usa]
        empresa = str(row[c_emp]).lower()
        if pd.isna(valor): return 0.0
        s = str(valor).replace('%', '').replace(',', '.').strip()
        try:
            n = float(s)
            if any(x in empresa for x in ["cardif", "scotiabank"]):
                return n / 10000.0 if n > 1.0 else n / 100.0
            return n / 100.0 if n > 1.0 else n
        except: return 0.0

    df['Usabilidad_Limpia'] = df.apply(limpiar_pct, axis=1)
    df['Anio_Limpio'] = pd.to_numeric(df[c_ani], errors='coerce').fillna(0).astype(int)
    df = df[df['Anio_Limpio'] > 2020].copy()
    df['Mes_Limpio'] = pd.to_numeric(df[c_mes], errors='coerce').fillna(0).astype(int)
    df['Empresa_Limpia'] = df[c_emp].astype(str).str.strip()
    df['Semana_Filtro'] = df[c_sem].astype(str).str.strip() if c_sem else "Mes Total"
    return df

try:
    df = load_data()
    if df.empty: st.stop()

    # --- ENCABEZADO: Título y Logo a la derecha ---
    col_titu, col_logo = st.columns([4, 1])
    with col_titu:
        st.markdown("<h1>Reporte de Usabilidad</h1>", unsafe_allow_html=True)
    with col_logo:
        if os.path.exists("image_e57c24.png"):
            st.markdown('<div style="text-align: right;">', unsafe_allow_html=True)
            st.image("image_e57c24.png", width=130)
            st.markdown('</div>', unsafe_allow_html=True)

    # --- SIDEBAR (FILTROS) ---
    with st.sidebar:
        st.markdown("### ⚙️ Configuración")
        empresas_unicas = sorted([e for e in df['Empresa_Limpia'].unique() if e != 'nan'])
        emp_sel = st.selectbox("Empresa Target", ["Todas las Empresas"] + empresas_unicas)
        anios_disponibles = sorted(df['Anio_Limpio'].unique(), reverse=True)
        anios_sel = st.multiselect("Comparativa Anual", anios_disponibles, default=anios_disponibles)
        meses_map = {1:'Ene', 2:'Feb', 3:'Mar', 4:'Abr', 5:'May', 6:'Jun', 7:'Jul', 8:'Ago', 9:'Set', 10:'Oct', 11:'Nov', 12:'Dic'}
        meses_sel = st.multiselect("Meses", sorted(meses_map.keys()), default=sorted(meses_map.keys()), format_func=lambda x: meses_map[x])
        opciones_raw = sorted(df['Semana_Filtro'].unique().tolist())
        opciones_vistas = ["Mes Total"] + [opt for opt in opciones_raw if "total" not in opt.lower()]
        seleccion_vista = st.selectbox("Detalle Temporal", opciones_vistas)

    st.markdown("---")

    # --- INDICADORES (GAUGES MÁS PEQUEÑOS Y CIRCULARES) ---
    colores_dict = {2024: "#F1FB8C", 2025: "#FF9F86", 2026: "#A9C1F5"}
    if anios_sel:
        cols_gauges = st.columns(len(anios_sel))
        for idx, anio in enumerate(sorted(anios_sel)):
            with cols_gauges[idx]:
                data_anio = df[df['Anio_Limpio'] == anio]
                if emp_sel != "Todas las Empresas":
                    data_anio = data_anio[data_anio['Empresa_Limpia'] == emp_sel]
                
                avg_val = data_anio['Usabilidad_Limpia'].mean()
                fig_g = go.Figure(go.Indicator(
                    mode="gauge+number", value=avg_val*100,
                    number={'suffix': "%", 'font': {'size': 26, 'color': '#1E293B'}, 'valueformat':'.1f'},
                    title={'text': f"Promedio {anio}", 'font': {'size': 16, 'color': '#475569'}},
                    gauge={'axis': {'range': [0, 100], 'tickfont': {'size': 10}}, 
                           'bar': {'color': colores_dict.get(anio, "#CBD5E1")},
                           'bgcolor': "white", 'bordercolor': "#E2E8F0"}
                ))
                fig_g.update_layout(height=170, margin=dict(l=20, r=20, t=40, b=10), paper_bgcolor='rgba(0,0,0,0)')
                st.plotly_chart(fig_g, use_container_width=True, key=f"g_{anio}")

    # --- GRÁFICO DE EVOLUCIÓN ESTRATÉGICA ---
    mask = (df['Anio_Limpio'].isin(anios_sel)) & (df['Mes_Limpio'].isin(meses_sel))
    if seleccion_vista != "Mes Total":
        mask = mask & (df['Semana_Filtro'] == seleccion_vista)
    
    df_f = df[mask].copy()
    if emp_sel != "Todas las Empresas":
        df_f = df_f[df_f['Empresa_Limpia'] == emp_sel]

    if not df_f.empty:
        st.markdown("### 📈 Evolución Estratégica")
        df_plot = df_f.groupby(['Mes_Limpio', 'Anio_Limpio'])['Usabilidad_Limpia'].mean().reset_index()
        
        fig_main = go.Figure()
        for a in sorted(anios_sel):
            df_a = df_plot[df_plot['Anio_Limpio'] == a].sort_values('Mes_Limpio')
            if not df_a.empty:
                x_names = [meses_map.get(m) for m in df_a['Mes_Limpio']]
                fig_main.add_trace(go.Scatter(
                    x=x_names, y=df_a['Usabilidad_Limpia'],
                    name=f"Año {a}", mode='lines+markers+text',
                    line=dict(color=colores_dict.get(a), width=4),
                    text=[f"{v:.1%}" for v in df_a['Usabilidad_Limpia']],
                    textposition="top center"
                ))
        
        fig_main.update_layout(
            paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)',
            yaxis=dict(tickformat=".0%", gridcolor='rgba(0,0,0,0.1)'),
            xaxis=dict(showgrid=False),
            legend=dict(orientation="h", y=1.1, x=0.5, xanchor="center")
        )
        st.plotly_chart(fig_main, use_container_width=True)

        # --- SECCIÓN DE INSIGHTS INTELIGENTES (RESTAURADA) ---
        st.markdown("### 🧠 Insights Estratégicos")
        c1, c2 = st.columns(2)
        with c1:
            mejor_mes_idx = df_f.groupby('Mes_Limpio')['Usabilidad_Limpia'].mean().idxmax()
            mejor_val = df_f.groupby('Mes_Limpio')['Usabilidad_Limpia'].mean().max()
            st.success(f"🚀 **Pico Máximo:** El mejor rendimiento fue en **{meses_map[mejor_mes_idx]}** con un **{mejor_val:.1%}**.")
            
            p_sem = df_f[df_f['Mes_Limpio'] <= 6]['Usabilidad_Limpia'].mean()
            s_sem = df_f[df_f['Mes_Limpio'] > 6]['Usabilidad_Limpia'].mean()
            if not pd.isna(s_sem):
                msj = "crecimiento" if s_sem > p_sem else "ajuste"
                st.info(f"📊 **Tendencia Semestral:** Se observa un **{msj}** en el segundo semestre vs el primero.")

        with c2:
            if len(anios_sel) >= 2:
                v_rec = df[df['Anio_Limpio'] == max(anios_sel)]['Usabilidad_Limpia'].mean()
                v_pre = df[df['Anio_Limpio'] == min(anios_sel)]['Usabilidad_Limpia'].mean()
                diff = (v_rec - v_pre) / (v_pre if v_pre != 0 else 1)
                st.warning(f"📈 **Variación Interanual:** La usabilidad ha cambiado un **{diff:+.1%}$ respecto al año base.")

        # --- RANKING DE EMPRESAS (RESTAURADO) ---
        if emp_sel == "Todas las Empresas":
            st.markdown("### 🏆 Top 5 Empresas con Mayor Usabilidad")
            top_5 = df_f.groupby('Empresa_Limpia')['Usabilidad_Limpia'].mean().nlargest(5).reset_index()
            top_5.columns = ['Empresa', 'Usabilidad Media']
            st.dataframe(top_5.style.format({'Usabilidad Media': '{:.2%}'}).background_gradient(cmap='Blues'), use_container_width=True)

except Exception as e:
    st.error(f"Error en el reporte: {e}")
