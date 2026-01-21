import streamlit as st
import pandas as pd
import plotly.graph_objects as go
import os

# 1. Configuración de página y Estilo Philosopher con Colores de Marca
st.set_page_config(page_title="Reporte de Usabilidad Holos", layout="wide")

# Paleta de colores extraída de la imagen:
# Azul Marino: #004A7C | Salmón: #FF8A71 | Amarillo/Verde: #E8FF70 | Fondo: #F8F9FA
st.markdown("""
    <link href="https://fonts.googleapis.com/css2?family=Philosopher:wght@400;700&display=swap" rel="stylesheet">
    <style>
        * { font-family: 'Philosopher', sans-serif !important; }
        .stApp { background-color: #F8F9FA; }
        .stSelectbox, .stMultiSelect { background-color: white; border-radius: 8px; border: 1px solid #004A7C; }
        h1 { color: #004A7C; font-weight: 700; font-size: 2.8rem !important; margin-bottom: 5px; }
        [data-testid="stSidebar"] { background-color: #FFFFFF; border-right: 1px solid #E0E0E0; }
        .stMarkdown h3 { color: #004A7C; }
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
            # Corrección Cardif/Scotiabank: 56 -> 0.56%
            if "cardif" in empresa or "scotiabank" in empresa:
                return n / 10000.0 if n > 1.0 else n / 100.0
            return n / 100.0 if n > 1.0 else n
        except: return 0.0

    df['Usabilidad_Limpia'] = df.apply(limpiar_pct, axis=1)
    df['Anio_Limpio'] = pd.to_numeric(df[c_ani], errors='coerce').fillna(0).astype(int)
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
        st.warning("No hay archivos CSV en la carpeta.")
        st.stop()

    # --- ENCABEZADO ---
    col_logo, col_tit, col_g1, col_g2, col_g3 = st.columns([0.6, 1.4, 1, 1, 1])
    
    with col_logo:
        st.image("image_e57c24.png", width=110)

    with col_tit:
        st.markdown("<h1>Reporte de Usabilidad</h1>", unsafe_allow_html=True)

    # --- SIDEBAR (Filtros Estilizados) ---
    with st.sidebar:
        st.markdown("### 🔍 Filtros")
        empresas_unicas = sorted([e for e in df['Empresa_Limpia'].unique() if e != 'nan'])
        emp_sel = st.selectbox("Empresa", ["Todas las Empresas"] + empresas_unicas)
        anios_sel = st.multiselect("Año", sorted(df['Anio_Limpio'].unique()), default=sorted(df['Anio_Limpio'].unique()))
        
        meses_map = {1:'Ene', 2:'Feb', 3:'Mar', 4:'Abr', 5:'May', 6:'Jun', 7:'Jul', 8:'Ago', 9:'Set', 10:'Oct', 11:'Nov', 12:'Dic'}
        meses_sel = st.multiselect("Mes", sorted(meses_map.keys()), default=[1], format_func=lambda x: meses_map[x])

        st.markdown("---")
        opciones_raw = sorted(df['Semana_Filtro'].unique().tolist())
        opciones_sin_total = [opt for opt in opciones_raw if "total" not in opt.lower()]
        opciones_menu = ["Acumulado"] + opciones_sin_total
        
        seleccion_vista = st.selectbox("Vista Temporal", opciones_menu)
        # Lógica: Si el usuario elige Acumulado, buscamos "Mes total" en el CSV
        filtro_real_semana = "Mes total" if seleccion_vista == "Acumulado" else seleccion_vista

    # --- INDICADORES SUPERIORES (GAUGES) ---
    def crear_gauge(anio, color, key):
        # Buscamos la fila "Mes total" para el acumulado arriba
        data_a = df[(df['Anio_Limpio'] == anio) & (df['Semana_Filtro'] == "Mes total")]
        
        if emp_sel != "Todas las Empresas":
            data_a = data_a[data_a['Empresa_Limpia'] == emp_sel]
        
        # Si no hay "Mes total", promediamos para no dejarlo vacío
        if data_a.empty:
            data_a = df[df['Anio_Limpio'] == anio]
            
        val = data_a['Usabilidad_Limpia'].mean()
        if pd.isna(val) or val == 0: return
        
        fig = go.Figure(go.Indicator(
            mode="gauge+number", value=val*100,
            number={'suffix': "%", 'font': {'size': 22, 'color': '#004A7C'}, 'valueformat':'.2f'},
            title={'text': f"Avg {anio}", 'font': {'size': 16, 'color': '#004A7C'}},
            gauge={
                'axis': {'range': [0, 100], 'tickwidth': 1},
                'bar': {'color': color},
                'bgcolor': "white",
                'borderwidth': 2,
                'bordercolor': "#E0E0E0"
            }
        ))
        fig.update_layout(height=180, margin=dict(l=25, r=25, t=50, b=10), paper_bgcolor='rgba(0,0,0,0)')
        st.plotly_chart(fig, use_container_width=True, key=key)

    with col_g1:
        if 2024 in anios_sel: crear_gauge(2024, "#004A7C", "g24") # Azul
    with col_g2:
        if 2025 in anios_sel: crear_gauge(2025, "#FF8A71", "g25") # Salmón
    with col_g3:
        if 2026 in anios_sel: crear_gauge(2026, "#E8FF70", "g26") # Amarillo Neón

    # --- GRÁFICO PRINCIPAL ---
    mask = (df['Anio_Limpio'].isin(anios_sel)) & \
           (df['Mes_Limpio'].isin(meses_sel)) & \
           (df['Semana_Filtro'] == filtro_real_semana)
    
    df_f = df[mask].copy()
    if emp_sel != "Todas las Empresas":
        df_f = df_f[df_f['Empresa_Limpia'] == emp_sel]

    if not df_f.empty:
        fig_main = go.Figure()
        colores_marca = {2024: "#004A7C", 2025: "#FF8A71", 2026: "#E8FF70"}
        eje_x = 'Empresa_Limpia' if emp_sel == "Todas las Empresas" else 'Mes_Limpio'
        
        for a in sorted(anios_sel):
            df_a = df_f[df_f['Anio_Limpio'] == a]
            if not df_a.empty:
                x_vals = df_a[eje_x] if emp_sel == "Todas las Empresas" else [meses_map.get(m) for m in df_a['Mes_Limpio']]
                fig_main.add_trace(go.Bar(
                    x=x_vals, y=df_a['Usabilidad_Limpia'],
                    name=f"Real {a}", 
                    marker_color=colores_marca.get(a),
                    text=[f"{v:.2%}" for v in df_a['Usabilidad_Limpia']], 
                    textposition='outside'
                ))
        
        fig_main.update_layout(
            paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='white', barmode='group',
            yaxis=dict(tickformat=".2%", gridcolor='#F0F0F0'),
            xaxis=dict(gridcolor='#F0F0F0'),
            legend=dict(orientation="h", y=1.2, x=0.5, xanchor="center")
        )
        st.plotly_chart(fig_main, use_container_width=True, key="main")
    else:
        st.info("No hay datos para esta selección. Prueba cambiando el Mes o seleccionando 'Acumulado'.")

except Exception as e:
    st.error(f"Error crítico: {e}")
