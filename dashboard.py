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

@st.cache_data(ttl=10) # Bajamos a 10 segundos para que refresque casi en tiempo real
def cargar_data():
    try:
        df1 = pd.read_csv(LINK_1)
        df2 = pd.read_csv(LINK_2)
        df = pd.concat([df1, df2], ignore_index=True)
        df.columns = [str(c).strip() for c in df.columns]
        
        # Mapeo ultra-flexible de columnas (Ajuste 1: más nombres posibles)
        c_usa = next((c for c in df.columns if any(x in c for x in ['%', 'Engage', 'Usabil'])), df.columns[7])
        c_emp = next((c for c in df.columns if any(x in c for x in ['Empresa', 'Nombre'])), df.columns[0])
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
        # Ajuste 2: Asegurar que detecte 2026 aunque esté como texto o número
        df['Anio_V'] = pd.to_numeric(df[c_ani], errors='coerce').fillna(0).astype(int)
        df['Mes_V'] = pd.to_numeric(df[c_mes], errors='coerce').fillna(0).astype(int)
        df['Empresa_V'] = df[c_emp].astype(str).str.strip()
        df['Semana_V'] = df[c_sem].astype(str).str.strip().fillna("S/N")
        
        return df, 'Empresa_V', 'Anio_V', 'Mes_V', 'Semana_V'
    except Exception as e:
        return pd.DataFrame(), str(e), None, None, None

df, col_emp, col_ani, col_mes, col_sem = cargar_data()

if not df.empty:
    with st.sidebar:
        st.markdown("### 🎛️ Filtros")
        tipo_vista = st.radio("Nivel de Análisis:", ["Ejecutivo (Cierres)", "Operativo (Semanal)"], index=1)
        
        lista_empresas = sorted([e for e in df[col_emp].unique() if str(e) not in ['nan', 'None', '0']])
        empresa_sel = st.selectbox("Empresa Target", ["Todas las Empresas"] + lista_empresas)
        
        anios_disp = sorted([a for a in df[col_ani].unique() if a > 2020], reverse=True)
        anios_sel = st.multiselect("Años", anios_disp, default=[2025, 2026] if 2026 in anios_disp else anios_disp)
        
        meses_map = {1:'Ene', 2:'Feb', 3:'Mar', 4:'Abr', 5:'May', 6:'Jun', 7:'Jul', 8:'Ago', 9:'Set', 10:'Oct', 11:'Nov', 12:'Dic'}
        meses_sel = st.multiselect("Meses", sorted(meses_map.keys()), default=[1, 2], format_func=lambda x: meses_map[x])

    st.markdown(f"<h1>📊 Reporte de Usabilidad: {empresa_sel}</h1>", unsafe_allow_html=True)

    # --- LÓGICA DE FILTRADO REFORZADA ---
    df_f = df[(df[col_ani].isin(anios_sel)) & (df[col_mes].isin(meses_sel))].copy()
    if empresa_sel != "Todas las Empresas":
        df_f = df_f[df_f[col_emp] == empresa_sel]

    # Ajuste 3: Si estamos en Operativo, mostramos TODO lo que no sea el total acumulado
    if tipo_vista == "Ejecutivo (Cierres)":
        df_vis = df_f[df_f[col_sem].str.contains('total|Total', case=False, na=False)]
    else:
        # En operativo mostramos las semanas; si la fila de febrero no dice nada en 'semana', igual la mostramos
        df_vis = df_f.copy()

    # --- VISUALIZACIÓN ---
    anios_activos = sorted(df_vis[col_ani].unique())
    if anios_activos:
        gauge_cols = st.columns(len(anios_activos))
        for i, anio in enumerate(anios_activos):
            with gauge_cols[i]:
                promedio = df_vis[df_vis[col_ani] == anio]['Usabilidad_V'].mean()
                fig_g = go.Figure(go.Indicator(
                    mode="gauge+number", value=(promedio or 0)*100,
                    number={'suffix': "%", 'font': {'size': 28}, 'valueformat': '.1f'},
                    title={'text': f"Media {anio}"},
                    gauge={'axis': {'range': [0, 100]}, 'bar': {'color': BLACK},
                           'steps': [{'range': [0, 100], 'color': SEA if anio == 2026 else CORAL}]}
                ))
                fig_g.update_layout(height=220, margin=dict(l=30, r=30, t=50, b=20), paper_bgcolor='rgba(0,0,0,0)')
                st.plotly_chart(fig_g, use_container_width=True)

    st.markdown(f"### 📈 Curva de Engagement ({tipo_vista})")
    if not df_vis.empty:
        df_ev = df_vis.groupby([col_ani, col_mes, col_sem])['Usabilidad_V'].mean().reset_index()
        df_ev = df_ev.sort_values([col_ani, col_mes]) 
        
        fig_line = go.Figure()
        for anio in anios_activos:
            df_a = df_ev[df_ev[col_ani] == anio]
            x_labels = [f"{meses_map.get(m)}-{s}" for m, s in zip(df_a[col_mes], df_a[col_sem])]
            fig_line.add_trace(go.Scatter(
                x=x_labels, y=df_a['Usabilidad_V'], name=f"Año {anio}",
                mode='lines+markers+text', text=[f"{v:.1%}" for v in df_a['Usabilidad_V']],
                textposition="top center"
            ))
        fig_line.update_layout(yaxis=dict(tickformat=".0%", range=[0, 1.1]), height=400)
        st.plotly_chart(fig_line, use_container_width=True)

    # TABLA DE VALIDACIÓN (Para que veas qué está leyendo el código)
    with st.expander("🔍 Auditoría de datos (Si ves esto vacío, revisa el Excel)"):
        st.write("Filas detectadas para los filtros seleccionados:")
        st.dataframe(df_vis[[col_emp, col_ani, col_mes, col_sem, 'Usabilidad_V']])
else:
    st.error("No se detectan datos. Revisa que en el Excel el Mes de Febrero sea '2' y el Año sea '2026'.")
