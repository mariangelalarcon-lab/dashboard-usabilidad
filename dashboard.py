import streamlit as st
import pandas as pd
import plotly.graph_objects as go
import os

# 1. Configuración y Estilo
st.set_page_config(page_title="Dashboard Holos", layout="wide")
st.markdown("<style>.stApp {background-color: #E3F2FD;}</style>", unsafe_allow_html=True)

def encontrar_columna(df, palabras_clave):
    for col in df.columns:
        for palabra in palabras_clave:
            if palabra.lower() in col.lower(): return col
    return None

@st.cache_data
def load_data():
    archivos_csv = [f for f in os.listdir('.') if f.endswith('.csv')]
    if not archivos_csv:
        return pd.DataFrame()
    
    lista_df = [pd.read_csv(f) for f in archivos_csv]
    df = pd.concat(lista_df, ignore_index=True)
    
    c_emp = encontrar_columna(df, ['Nombre', 'Empresa'])
    c_usa = encontrar_columna(df, ['% Usabilidad', 'Engagement'])
    c_met = encontrar_columna(df, ['Meta en %', 'Meta %'])
    c_mes = encontrar_columna(df, ['Inicio del Mes', 'Mes'])
    c_ani = encontrar_columna(df, ['Inicio de Año', 'Año'])
    c_sem = encontrar_columna(df, ['Semana', 'Week', 'Desglose']) 

    def limpiar_pct(valor):
        if pd.isna(valor): return 0.0
        s = str(valor).replace('%', '').replace(',', '.').strip()
        try:
            n = float(s)
            return n / 100.0 if n > 1.0 else n
        except: return 0.0

    df['Usabilidad_Limpia'] = df[c_usa].apply(limpiar_pct)
    df['Meta_Limpia'] = df[c_met].apply(limpiar_pct)
    df['Anio_Limpio'] = pd.to_numeric(df[c_ani], errors='coerce').fillna(0).astype(int)
    df['Mes_Limpio'] = pd.to_numeric(df[c_mes], errors='coerce').fillna(0).astype(int)
    df['Empresa_Limpia'] = df[c_emp].astype(str).str.strip()
    
    # Normalizamos la columna de semanas
    if c_sem:
        df['Semana_Filtro'] = df[c_sem].astype(str).str.strip()
    else:
        # Si no existe la columna en años viejos, asumimos que es el dato total
        df['Semana_Filtro'] = "Mes total"

    return df

try:
    df = load_data()
    if df.empty:
        st.warning("Sube tu archivo CSV a GitHub.")
        st.stop()

    # --- ENCABEZADO ---
    col_logo, col_tit, col_g1, col_g2, col_g3 = st.columns([1, 1.5, 1, 1, 1])
    with col_logo:
        st.image("https://www.holos.club/_next/static/media/logo-black.68e7f8e7.svg", width=120)
    with col_tit:
        st.title("Reporte Holos")

    # --- FILTROS SIDEBAR ---
    with st.sidebar:
        st.header("Configuración")
        lista_emp = ["Todas las Empresas"] + sorted(df['Empresa_Limpia'].unique().tolist())
        emp_sel = st.selectbox("Empresa", lista_emp)
        
        anios_disp = sorted(df['Anio_Limpio'].unique())
        anios_sel = st.multiselect("Años", anios_disp, default=anios_disp)
        
        meses_map = {1:'Ene', 2:'Feb', 3:'Mar', 4:'Abr', 5:'May', 6:'Jun', 7:'Jul', 8:'Ago', 9:'Set', 10:'Oct', 11:'Nov', 12:'Dic'}
        meses_sel = st.multiselect("Meses", sorted(meses_map.keys()), default=sorted(meses_map.keys()), format_func=lambda x: meses_map[x])

        # FILTRO DE SEMANAS (Aparece si hay datos de semanas disponibles)
        semana_sel = "Mes total"
        opciones_sem = sorted(df['Semana_Filtro'].unique().tolist())
        if len(opciones_sem) > 1:
            st.markdown("---")
            st.subheader("Desglose de Tiempo")
            # Ponemos 'Mes total' como el valor por defecto si existe
            idx_default = opciones_sem.index("Mes total") if "Mes total" in opciones_sem else 0
            semana_sel = st.selectbox("Ver detalle por:", opciones_sem, index=idx_default)

    # --- PROCESAMIENTO DE DATOS ---
    # 1. Filtro base por año/mes
    mask = (df['Anio_Limpio'].isin(anios_sel)) & (df['Mes_Limpio'].isin(meses_sel))
    df_base = df[mask].copy()
    
    # 2. Aplicamos el filtro de semana (Si el año es 2026 o tiene semanas, filtramos. Si no, dejamos pasar)
    # Esto permite que 2024/2025 sigan funcionando aunque no tengan columna de semana
    df_f = df_base[ (df_base['Semana_Filtro'] == semana_sel) | (~df_base['Semana_Filtro'].isin(opciones_sem)) ]

    # --- INDICADORES CIRCULARES (Siempre sobre el 'Mes total') ---
    def crear_gauge(anio, color):
        # Para el promedio anual usamos solo 'Mes total' para que el dato sea verídico
        data_gauge = df[ (df['Anio_Limpio'] == anio) & (df['Semana_Filtro'] == "Mes total") ]
        val = data_gauge['Usabilidad_Limpia'].mean()
        if pd.isna(val) or val == 0: return None
        fig = go.Figure(go.Indicator(
            mode="gauge+number", value=val*100,
            number={'suffix': "%", 'font': {'size': 18}},
            title={'text': f"Avg {anio}", 'font': {'size': 12}},
            gauge={'axis': {'range': [0, 100]}, 'bar': {'color': color}, 'bgcolor': "white"}
        ))
        fig.update_layout(height=130, margin=dict(l=10, r=10, t=30, b=10), paper_bgcolor='rgba(0,0,0,0)')
        return fig

    if emp_sel == "Todas las Empresas":
        g24 = crear_gauge(2024, "#1f77b4")
        if g24: with col_g1: st.plotly_chart(g24, use_container_width=True, key="c24")
        g25 = crear_gauge(2025, "#FF4B4B")
        if g25: with col_g2: st.plotly_chart(g25, use_container_width=True, key="c25")
        g26 = crear_gauge(2026, "#00CC96")
        if g26: with col_g3: st.plotly_chart(g26, use_container_width=True, key="c26")
        
        df_plot = df_f.groupby(['Anio_Limpio', 'Mes_Limpio']).agg({'Usabilidad_Limpia': 'mean', 'Meta_Limpia': 'mean'}).reset_index()
    else:
        df_ind = df_f[df_f['Empresa_Limpia'] == emp_sel]
        df_plot = df_ind.sort_values(['Anio_Limpio', 'Mes_Limpio'])

    # --- GRÁFICO PRINCIPAL ---
    if not df_plot.empty:
        fig_main = go.Figure()
        colores_map = {2024: "#1f77b4", 2025: "#FF4B4B", 2026: "#00CC96"}
        for a in anios_sel:
            d_anio = df_plot[df_plot['Anio_Limpio'] == a]
            if not d_anio.empty:
                mx = [meses_map.get(m) for m in d_anio['Mes_Limpio']]
                # Etiqueta dinámica para saber qué estamos viendo
                label_vista = f" ({semana_sel})" if semana_sel != "Mes total" else ""
                
                fig_main.add_trace(go.Bar(
                    x=mx, y=d_anio['Usabilidad_Limpia'], 
                    name=f"Real {a}{label_vista}", 
                    marker_color=colores_map.get(a, "gray"), 
                    text=[f"{v:.1%}" for v in d_anio['Usabilidad_Limpia']], 
                    textposition='outside'
                ))
                fig_main.add_trace(go.Scatter(x=mx, y=d_anio['Meta_Limpia'], name=f"Meta {a}", line=dict(dash='dash', color='gray')))
        
        fig_main.update_layout(
            paper_bgcolor='rgba(0,0,0,0)', 
            plot_bgcolor='white', 
            barmode='group', 
            yaxis=dict(tickformat=".0%", range=[0, 1.1]),
            legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1)
        )
        st.plotly_chart(fig_main, use_container_width=True, key="main_chart_weeks")
    else:
        st.info("Selecciona parámetros para mostrar el gráfico.")

except Exception as e:
    st.error(f"Error en el procesamiento: {e}")
