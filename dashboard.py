import streamlit as st
import pandas as pd
import plotly.graph_objects as go
import os

# 1. Configuración de página y Estilo Philosopher
st.set_page_config(page_title="Reporte de Usabilidad Holos", layout="wide")

st.markdown("""
    <link href="https://fonts.googleapis.com/css2?family=Philosopher:wght@400;700&display=swap" rel="stylesheet">
    <style>
        * { font-family: 'Philosopher', sans-serif !important; }
        .stApp { background-color: #E3F2FD; }
        .stSelectbox, .stMultiSelect { background-color: white; border-radius: 10px; }
        h1 { color: #0D47A1; font-weight: 700; font-size: 3rem !important; }
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
    c_met = encontrar_columna(df, ['Meta en %', 'Meta %'])
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
            # Solo para Cardif/Scotiabank: 56 -> 0.0056 (0.56%)
            if "cardif" in empresa or "scotiabank" in empresa:
                return n / 10000.0 if n > 1.0 else n / 100.0
            return n / 100.0 if n > 1.0 else n
        except: return 0.0

    df['Usabilidad_Limpia'] = df.apply(limpiar_pct, axis=1)
    df['Meta_Limpia'] = df[c_met].apply(lambda x: float(str(x).replace('%','').replace(',','.'))/100 if pd.notna(x) else 0.0)
    df['Anio_Limpio'] = pd.to_numeric(df[c_ani], errors='coerce').fillna(0).astype(int)
    df = df[df['Anio_Limpio'] > 2020].copy()
    df['Mes_Limpio'] = pd.to_numeric(df[c_mes], errors='coerce').fillna(0).astype(int)
    df['Empresa_Limpia'] = df[c_emp].astype(str).str.strip()
    
    # Normalización de semanas para el filtro Acumulado
    if c_sem:
        df['Semana_Filtro'] = df[c_sem].astype(str).str.strip()
    else:
        df['Semana_Filtro'] = "Mes total"
    return df

try:
    df = load_data()
    if df.empty:
        st.warning("Sube tus archivos CSV para comenzar.")
        st.stop()

    # --- ENCABEZADO ---
    col_logo, col_tit, col_g1, col_g2, col_g3 = st.columns([0.6, 1.6, 1, 1, 1])
    
    with col_logo:
        # Intentar cargar el logo que subiste (debe llamarse logo.png en tu repo)
        if os.path.exists("logo.png"):
            st.image("logo.png", width=120)
        else:
            st.image("https://www.holos.club/_next/static/media/logo-black.68e7f8e7.svg", width=120)

    with col_tit:
        st.markdown("<h1>Reporte de Usabilidad</h1>", unsafe_allow_html=True)

    # --- SIDEBAR ---
    with st.sidebar:
        st.markdown("### ⚙️ Configuración")
        empresas_unicas = sorted([e for e in df['Empresa_Limpia'].unique() if e != 'nan'])
        emp_sel = st.selectbox("Empresa", ["Todas las Empresas"] + empresas_unicas)
        anios_sel = st.multiselect("Año", sorted(df['Anio_Limpio'].unique()), default=sorted(df['Anio_Limpio'].unique()))
        
        meses_map = {1:'Ene', 2:'Feb', 3:'Mar', 4:'Abr', 5:'May', 6:'Jun', 7:'Jul', 8:'Ago', 9:'Set', 10:'Oct', 11:'Nov', 12:'Dic'}
        meses_sel = st.multiselect("Mes", sorted(meses_map.keys()), default=[max(meses_map.keys())], format_func=lambda x: meses_map[x])

        st.markdown("---")
        opciones_sem = sorted(df['Semana_Filtro'].unique().tolist())
        # Forzar que aparezca 'Acumulado'
        opciones_finales = ["Acumulado"] + [opt for opt in opciones_sem if "total" not in opt.lower()]
        seleccion_vista = st.selectbox("Vista Temporal", opciones_finales)
        semana_busqueda = "Mes total" if seleccion_vista == "Acumulado" else seleccion_vista

    # --- INDICADORES (GAUGES) ---
    def crear_gauge(anio, color):
        # El indicador siempre busca el dato "Mes total" para el acumulado anual
        data_a = df[(df['Anio_Limpio'] == anio) & (df['Semana_Filtro'].str.contains('total|Mes total|1era Semana|2da Semana|3era Semana|4ta semana', case=False, na=False))]
        
        if emp_sel != "Todas las Empresas":
            data_a = data_a[data_a['Empresa_Limpia'] == emp_sel]
        
        # Si no hay datos específicos de "total", promediamos lo que haya para ese año
        if data_a.empty:
            data_a = df[df['Anio_Limpio'] == anio]
            
        val = data_a['Usabilidad_Limpia'].mean()
        if pd.isna(val) or val == 0: return None
        
        fig = go.Figure(go.Indicator(
            mode="gauge+number", value=val*100,
            number={'suffix': "%", 'font': {'size': 20}, 'valueformat':'.2f'},
            title={'text': f"Avg {anio}", 'font': {'size': 16, 'color': '#0D47A1'}},
            gauge={'axis': {'range': [0, 100]}, 'bar': {'color': color}}
        ))
        fig.update_layout(height=180, margin=dict(l=20, r=20, t=50, b=10), paper_bgcolor='rgba(0,0,0,0)')
        return fig

    with col_g1:
        if 2024 in anios_sel:
            g24 = crear_gauge(2024, "#1f77b4")
            if g24: st.plotly_chart(g24, use_container_width=True, key="k24")
    with col_g2:
        if 2025 in anios_sel:
            g25 = crear_gauge(2025, "#FF4B4B")
            if g25: st.plotly_chart(g25, use_container_width=True, key="k25")
    with col_g3:
        if 2026 in anios_sel:
            g26 = crear_gauge(2026, "#00CC96")
            if g26: st.plotly_chart(g26, use_container_width=True, key="k26")

    # --- GRÁFICO PRINCIPAL ---
    # Filtrar por semana/acumulado de forma flexible
    if semana_busqueda == "Mes total":
        mask = (df['Anio_Limpio'].isin(anios_sel)) & (df['Mes_Limpio'].isin(meses_sel)) & (df['Semana_Filtro'].str.contains('total', case=False))
    else:
        mask = (df['Anio_Limpio'].isin(anios_sel)) & (df['Mes_Limpio'].isin(meses_sel)) & (df['Semana_Filtro'] == semana_busqueda)
    
    df_f = df[mask].copy()
    if emp_sel != "Todas las Empresas":
        df_f = df_f[df_f['Empresa_Limpia'] == emp_sel]

    if not df_f.empty:
        fig_main = go.Figure()
        colors = {2024: "#1f77b4", 2025: "#FF4B4B", 2026: "#00CC96"}
        eje_x = 'Empresa_Limpia' if emp_sel == "Todas las Empresas" else 'Mes_Limpio'
        
        for a in sorted(anios_sel):
            df_a = df_f[df_f['Anio_Limpio'] == a]
            if not df_a.empty:
                x_vals = df_a[eje_x] if emp_sel == "Todas las Empresas" else [meses_map.get(m) for m in df_a['Mes_Limpio']]
                fig_main.add_trace(go.Bar(
                    x=x_vals, y=df_a['Usabilidad_Limpia'],
                    name=f"Año {a}", marker_color=colors.get(a),
                    text=[f"{v:.2%}" for v in df_a['Usabilidad_Limpia']], textposition='outside'
                ))
        
        fig_main.update_layout(
            paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='white', barmode='group',
            yaxis=dict(tickformat=".2%", title="Nivel de Usabilidad", range=[0, max(df_f['Usabilidad_Limpia'].max()*1.2, 0.05)]),
            xaxis=dict(title="Empresas" if emp_sel == "Todas las Empresas" else "Meses"),
            legend=dict(orientation="h", y=1.2)
        )
        st.plotly_chart(fig_main, use_container_width=True, key="main")
    else:
        st.info("💡 Consejo: Si no ves datos en 'Acumulado', verifica que tus registros de 2026 tengan una fila llamada exactamente 'Mes total'.")

except Exception as e:
    st.error(f"Error en el dashboard: {e}")
