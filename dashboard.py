import streamlit as st
import pandas as pd
import plotly.graph_objects as go

# 1. CONFIGURACIÓN DE PÁGINA
st.set_page_config(page_title="Holos | BI Dashboard", layout="wide")

# Enlaces de datos
LINK_1 = "https://docs.google.com/spreadsheets/d/e/2PACX-1vSWiXR7BLxwzX2wtD_uF59pvxtus8BL5iqgymKSh2-Llwt6smOJzR7ROUxICr57DA/pub?gid=1638907402&single=true&output=csv"
LINK_2 = "https://docs.google.com/spreadsheets/d/e/2PACX-1vSWiXR7BLxwzX2wtD_uF59pvxtus8BL5iqgymKSh2-Llwt6smOJzR7ROUxICr57DA/pub?gid=1341962834&single=true&output=csv"

# Paleta de Colores Holos
SKY, LEAF, SEA, CORAL, BLACK = "#D1E9F6", "#F1FB8C", "#A9C1F5", "#FF9F86", "#000000"

@st.cache_data(ttl=60)
def cargar_data():
    try:
        df1 = pd.read_csv(LINK_1)
        df2 = pd.read_csv(LINK_2)
        df = pd.concat([df1, df2], ignore_index=True)
        df.columns = [str(c).strip() for c in df.columns]
        
        # Identificación de columnas clave
        c_emp = next((c for c in df.columns if 'Empresa' in c), df.columns[0])
        c_sem = next((c for c in df.columns if 'Semana' in c), None)
        c_col = next((c for c in df.columns if 'Colaboradores' in c), None)
        c_uti = next((c for c in df.columns if 'utilizaron' in c), None)
        c_mes = next((c for c in df.columns if 'Mes' in c and 'total' not in c.lower()), None)
        c_ani = next((c for c in df.columns if 'Año' in c or 'Anio' in c), None)
        c_usa = next((c for c in df.columns if '%' in c or 'Usabilidad' in c), None)

        # Limpieza y Conversión
        df['Colab'] = pd.to_numeric(df[c_col], errors='coerce').fillna(0)
        df['Util'] = pd.to_numeric(df[c_uti], errors='coerce').fillna(0)
        df['Anio'] = pd.to_numeric(df[c_ani], errors='coerce').fillna(0).astype(int)
        df['Mes'] = pd.to_numeric(df[c_mes], errors='coerce').fillna(0).astype(int)
        df['Empresa'] = df[c_emp].astype(str).str.strip()
        df['Semana_Txt'] = df[c_sem].astype(str).str.lower().str.strip() if c_sem else ""

        def limpiar_porcentaje(val):
            try:
                if pd.isna(val): return 0.0
                s = str(val).replace('%', '').replace(',', '.').strip()
                n = float(s)
                return n / 100.0 if n > 1.1 else n
            except: return 0.0

        df['Usabilidad_Directa'] = df[c_usa].apply(limpiar_porcentaje)
        
        return df
    except Exception as e:
        st.error(f"Error cargando base: {e}")
        return pd.DataFrame()

df = cargar_data()

if not df.empty:
    # --- SIDEBAR PROFESIONAL ---
    with st.sidebar:
        st.image("https://holos.la/wp-content/uploads/2022/07/logo-holos.png", width=150) # Logo genérico
        st.markdown("---")
        
        # MODO DE VISTA (El Switch solicitado)
        modo_vista = st.radio("🔍 Nivel de Análisis", ["Ejecutivo (Cierres)", "Operativo (Semanal)"])
        
        st.markdown("---")
        empresa_sel = st.selectbox("Empresa Target", ["Todas las Empresas"] + sorted(df['Empresa'].unique()))
        anios_sel = st.multiselect("Años", sorted(df['Anio'].unique(), reverse=True), default=[2025, 2026])
        meses_map = {1:'Ene', 2:'Feb', 3:'Mar', 4:'Abr', 5:'May', 6:'Jun', 7:'Jul', 8:'Ago', 9:'Set', 10:'Oct', 11:'Nov', 12:'Dic'}
        meses_sel = st.multiselect("Meses", sorted(meses_map.keys()), default=list(meses_map.keys()), format_func=lambda x: meses_map[x])

    # --- TÍTULO DINÁMICO ---
    st.markdown(f"<h1>Dashboard Holos: <span style='color:{CORAL}'>{empresa_sel}</span></h1>", unsafe_allow_html=True)
    st.info(f"Modo actual: **{modo_vista}**")

    # --- FILTRADO DE JERARQUÍA ---
    df_f = df[(df['Anio'].isin(anios_sel)) & (df['Mes'].isin(meses_sel))].copy()
    
    if empresa_sel != "Todas las Empresas":
        df_f = df_f[df_f['Empresa'] == empresa_sel]

    # Lógica de Selección de Filas según el Modo
    if modo_vista == "Ejecutivo (Cierres)":
        # Buscamos filas que contengan "total"
        df_vis = df_f[df_f['Semana_Txt'].str.contains('total', na=False)]
        # Si por algo no hay filas de total, tomamos la última del mes
        if df_vis.empty:
            df_vis = df_f.sort_values(['Anio', 'Mes']).groupby(['Empresa', 'Anio', 'Mes']).tail(1)
    else:
        # Modo Operativo: Mostramos todo lo que no sea total (las semanas)
        df_vis = df_f[~df_f['Semana_Txt'].str.contains('total', na=False)]
        if df_vis.empty: df_vis = df_f # Fallback

    # --- INDICADORES (GAUGES) ---
    st.markdown("### Salud de la Cuenta (Promedio de Cierre)")
    anios_presentes = sorted(df_vis['Anio'].unique())
    colores_anios = {2024: LEAF, 2025: CORAL, 2026: SEA}
    
    if not df_vis.empty:
        cols = st.columns(len(anios_presentes))
        for i, a in enumerate(anios_presentes):
            with cols[i]:
                df_a = df_vis[df_vis['Anio'] == a]
                # Lógica sugerida: Promedio de los porcentajes individuales (el 32.7% de tu Excel)
                valor_final = df_a['Usabilidad_Directa'].mean()
                
                fig = go.Figure(go.Indicator(
                    mode="gauge+number", value=valor_final*100,
                    number={'suffix': "%", 'valueformat': '.2f', 'font': {'size': 35}},
                    title={'text': f"Media {a}", 'font': {'size': 20}},
                    gauge={'axis': {'range': [0, 100]}, 'bar': {'color': BLACK},
                           'steps': [{'range': [0, 100], 'color': colores_anios.get(a, SKY)}]}
                ))
                fig.update_layout(height=280, margin=dict(l=30, r=30, t=50, b=20), paper_bgcolor='rgba(0,0,0,0)')
                st.plotly_chart(fig, use_container_width=True, key=f"gauge_{a}")

    # --- GRÁFICA DE TENDENCIA ---
    st.markdown(f"### Evolución {modo_vista}")
    if not df_vis.empty:
        fig_l = go.Figure()
        for a in anios_presentes:
            df_p = df_vis[df_vis['Anio'] == a].sort_values(['Mes'])
            
            # En modo operativo, queremos ver el detalle por semana si existe
            x_axis = [f"{meses_map[m]} - {s}" if modo_vista == "Operativo (Semanal)" else meses_map[m] 
                     for m, s in zip(df_p['Mes'], df_p['Semana_Txt'])]
            
            fig_l.add_trace(go.Scatter(
                x=x_axis, y=df_p['Usabilidad_Directa'],
                name=f"Año {a}", mode='lines+markers+text',
                text=[f"{v:.1%}" for v in df_p['Usabilidad_Directa']], textposition="top center",
                line=dict(color=colores_anios.get(a, BLACK), width=3)
            ))
        
        fig_l.update_layout(yaxis=dict(tickformat=".0%", range=[0, 1.1]), height=450, 
                          paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)',
                          legend=dict(orientation="h", y=1.1, x=0.5, xanchor="center"))
        st.plotly_chart(fig_l, use_container_width=True)

    # --- TABLA DE CONTROL OPERATIVO ---
    st.markdown("### 📋 Detalle de Registros")
    st.write("Esta tabla muestra los datos exactos que están alimentando los gráficos de arriba.")
    st.dataframe(df_vis[['Empresa', 'Anio', 'Mes', 'Semana_Txt', 'Usabilidad_Directa']], use_container_width=True)

else:
    st.warning("No hay datos disponibles para los filtros seleccionados.")
