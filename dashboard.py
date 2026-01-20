import streamlit as st
import pandas as pd
import plotly.graph_objects as go
import os

# 1. Configuración de página
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
    if not archivos_csv: return pd.DataFrame()
    
    lista_df = [pd.read_csv(f) for f in archivos_csv]
    df = pd.concat(lista_df, ignore_index=True)
    
    c_emp = encontrar_columna(df, ['Nombre', 'Empresa'])
    c_usa = encontrar_columna(df, ['% Usabilidad', 'Engagement'])
    c_met = encontrar_columna(df, ['Meta en %', 'Meta %'])
    c_mes = encontrar_columna(df, ['Inicio del Mes', 'Mes'])
    c_ani = encontrar_columna(df, ['Inicio de Año', 'Año'])
    c_sem = encontrar_columna(df, ['Semana', 'Desglose']) 

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
    # Filtro para eliminar años basura como 1899
    df = df[df['Anio_Limpio'] > 2020].copy()
    
    df['Mes_Limpio'] = pd.to_numeric(df[c_mes], errors='coerce').fillna(0).astype(int)
    df['Empresa_Limpia'] = df[c_emp].astype(str).str.strip()
    
    if c_sem:
        df['Semana_Filtro'] = df[c_sem].astype(str).str.strip()
    else:
        df['Semana_Filtro'] = "Mes total"

    return df

try:
    df = load_data()
    if df.empty:
        st.warning("No hay datos disponibles.")
        st.stop()

    # --- ENCABEZADO ---
    col_logo, col_tit, col_g1, col_g2, col_g3 = st.columns([0.8, 1.2, 1, 1, 1])
    with col_logo:
        st.image("https://www.holos.club/_next/static/media/logo-black.68e7f8e7.svg", width=120)
    with col_tit:
        st.title("Reporte Holos")

    # --- SIDEBAR ---
    with st.sidebar:
        st.header("Configuración")
        empresas_unicas = sorted([e for e in df['Empresa_Limpia'].unique() if e != 'nan'])
        emp_sel = st.selectbox("Empresa", ["Todas las Empresas"] + empresas_unicas)
        
        anios_disp = sorted(df['Anio_Limpio'].unique())
        anios_sel = st.multiselect("Años", anios_disp, default=anios_disp)
        
        meses_map = {1:'Ene', 2:'Feb', 3:'Mar', 4:'Abr', 5:'May', 6:'Jun', 7:'Jul', 8:'Ago', 9:'Set', 10:'Oct', 11:'Nov', 12:'Dic'}
        meses_sel = st.multiselect("Meses", sorted(meses_map.keys()), default=[max(meses_map.keys())], format_func=lambda x: meses_map[x])

        opciones_sem = sorted(df['Semana_Filtro'].unique().tolist())
        # Buscamos 'Mes total' de forma flexible
        val_default_sem = next((x for x in opciones_sem if "total" in x.lower()), opciones_sem[0] if opciones_sem else "Mes total")
        
        st.markdown("---")
        st.subheader("Desglose de Tiempo")
        semana_sel = st.selectbox("Ver detalle por:", opciones_sem, index=opciones_sem.index(val_default_sem))

    # --- INDICADORES (Gauges) ---
    def crear_gauge(anio, color):
        # Para el promedio usamos siempre la fila de 'Total'
        data_a = df[(df['Anio_Limpio'] == anio) & (df['Semana_Filtro'].str.contains('total', case=False, na=False))]
        if emp_sel != "Todas las Empresas":
            data_a = data_a[data_a['Empresa_Limpia'] == emp_sel]
        
        val = data_a['Usabilidad_Limpia'].mean()
        if pd.isna(val) or val == 0: return None
        
        fig = go.Figure(go.Indicator(
            mode="gauge+number", value=val*100,
            number={'suffix': "%", 'font': {'size': 17}, 'valueformat':'.1f'},
            title={'text': f"Avg {anio}", 'font': {'size': 12}},
            gauge={'axis': {'range': [0, 100]}, 'bar': {'color': color}}
        ))
        fig.update_layout(height=140, margin=dict(l=10, r=10, t=40, b=10), paper_bgcolor='rgba(0,0,0,0)')
        return fig

    with col_g1:
        g24 = crear_gauge(2024, "#1f77b4")
        if g24: st.plotly_chart(g24, use_container_width=True, key="g24")
    with col_g2:
        g25 = crear_gauge(2025, "#FF4B4B")
        if g25: st.plotly_chart(g25, use_container_width=True, key="g25")
    with col_g3:
        g26 = crear_gauge(2026, "#00CC96")
        if g26: st.plotly_chart(g26, use_container_width=True, key="g26")

    # --- FILTRADO PARA GRÁFICO ---
    mask = (df['Anio_Limpio'].isin(anios_sel)) & (df['Mes_Limpio'].isin(meses_sel)) & (df['Semana_Filtro'] == semana_sel)
    df_f = df[mask].copy()

    # --- LÓGICA DE GRÁFICO DINÁMICO ---
    fig_main = go.Figure()
    colores_map = {2024: "#1f77b4", 2025: "#FF4B4B", 2026: "#00CC96"}

    if emp_sel == "Todas las Empresas":
        # Eje X = Empresas para comparar
        for a in sorted(anios_sel):
            df_a = df_f[df_f['Anio_Limpio'] == a].groupby('Empresa_Limpia')['Usabilidad_Limpia'].mean().reset_index()
            if not df_a.empty:
                fig_main.add_trace(go.Bar(
                    x=df_a['Empresa_Limpia'], y=df_a['Usabilidad_Limpia'],
                    name=f"Real {a}", marker_color=colores_map.get(a),
                    text=[f"{v:.1%}" for v in df_a['Usabilidad_Limpia']], textposition='outside'
                ))
    else:
        # Eje X = Meses para ver evolución de UNA empresa
        df_ind = df_f[df_f['Empresa_Limpia'] == emp_sel]
        for a in sorted(anios_sel):
            df_a = df_ind[df_ind['Anio_Limpio'] == a].sort_values('Mes_Limpio')
            if not df_a.empty:
                meses_x = [meses_map.get(m) for m in df_a['Mes_Limpio']]
                fig_main.add_trace(go.Bar(
                    x=meses_x, y=df_a['Usabilidad_Limpia'],
                    name=f"Real {a}", marker_color=colores_map.get(a),
                    text=[f"{v:.1%}" for v in df_a['Usabilidad_Limpia']], textposition='outside'
                ))

    fig_main.update_layout(
        paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='white', barmode='group',
        yaxis=dict(tickformat=".0%", range=[0, 1.1]),
        xaxis=dict(title="Empresas" if emp_sel == "Todas las Empresas" else "Meses")
    )
    st.plotly_chart(fig_main, use_container_width=True, key="main_viz")

except Exception as e:
    st.error(f"Error: {e}")
