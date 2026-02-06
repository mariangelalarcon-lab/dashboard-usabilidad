import streamlit as st
import pandas as pd
import plotly.graph_objects as go

# 1. Configuración de pantalla
st.set_page_config(page_title="Holos | BI", layout="wide")

# Enlaces de datos
LINK_1 = "https://docs.google.com/spreadsheets/d/e/2PACX-1vSWiXR7BLxwzX2wtD_uF59pvxtus8BL5iqgymKSh2-Llwt6smOJzR7ROUxICr57DA/pub?gid=1638907402&single=true&output=csv"
LINK_2 = "https://docs.google.com/spreadsheets/d/e/2PACX-1vSWiXR7BLxwzX2wtD_uF59pvxtus8BL5iqgymKSh2-Llwt6smOJzR7ROUxICr57DA/pub?gid=1341962834&single=true&output=csv"

# Colores Holos
SKY, LEAF, SEA, CORAL, BLACK, WHITE = "#D1E9F6", "#F1FB8C", "#A9C1F5", "#FF9F86", "#000000", "#FFFFFF"

@st.cache_data(ttl=30) # Cache bajo para ver cambios de inmediato
def cargar_data():
    try:
        df1 = pd.read_csv(LINK_1)
        df2 = pd.read_csv(LINK_2)
        df = pd.concat([df1, df2], ignore_index=True)
        df.columns = [str(c).strip() for c in df.columns]
        
        # Identificación robusta de columnas
        c_usa = next((c for c in df.columns if '%' in c or 'Usabilidad' in c or 'Engagement' in c), None)
        c_emp = next((c for c in df.columns if 'Empresa' in c), df.columns[0])
        c_mes = next((c for c in df.columns if 'Mes' in c and 'total' not in c.lower()), None)
        c_ani = next((c for c in df.columns if 'Año' in c or 'Anio' in c), None)
        c_sem = next((c for c in df.columns if 'Semana' in c), None)

        def limpiar_num(val):
            try:
                if pd.isna(val): return 0.0
                s = str(val).replace('%', '').replace(',', '.').strip()
                n = float(s)
                return n / 100.0 if n > 1.1 else n
            except: return 0.0

        df['Usabilidad_V'] = df[c_usa].apply(limpiar_num)
        df['Anio_V'] = pd.to_numeric(df[c_ani], errors='coerce').fillna(0).astype(int)
        df['Mes_V'] = pd.to_numeric(df[c_mes], errors='coerce').fillna(0).astype(int)
        df['Empresa_V'] = df[c_emp].astype(str).str.strip()
        df['Semana_V'] = df[c_sem].astype(str).str.strip() if c_sem else "Mes total"
        
        return df, 'Empresa_V', 'Anio_V', 'Mes_V'
    except Exception as e:
        return pd.DataFrame(), str(e), None, None

df, col_emp, col_ani, col_mes = cargar_data()

if not df.empty:
    with st.sidebar:
        st.header("🎛️ Filtros")
        lista_empresas = sorted([e for e in df[col_emp].unique() if str(e) not in ['nan', 'None']])
        empresa_sel = st.selectbox("Empresa Target", ["Todas las Empresas"] + lista_empresas)
        anios_disp = sorted([a for a in df[col_ani].unique() if a > 2020], reverse=True)
        anios_sel = st.multiselect("Años", anios_disp, default=anios_disp)
        meses_map = {1:'Ene', 2:'Feb', 3:'Mar', 4:'Abr', 5:'May', 6:'Jun', 7:'Jul', 8:'Ago', 9:'Set', 10:'Oct', 11:'Nov', 12:'Dic'}
        meses_sel = st.multiselect("Meses", sorted(meses_map.keys()), default=sorted(meses_map.keys()), format_func=lambda x: meses_map[x])

    st.title(f"📊 Reporte: {empresa_sel}")

    # --- FILTRADO INTELIGENTE (Prioriza 'Mes total' como en tu Excel) ---
    df_f = df[(df[col_ani].isin(anios_sel)) & (df[col_mes].isin(meses_sel))].copy()
    
    # Si existen registros de 'Mes total', usamos esos para que el promedio no baje
    if "Mes total" in df_f['Semana_V'].values:
        df_f = df_f[df_f['Semana_V'] == "Mes total"]

    if empresa_sel != "Todas las Empresas":
        df_f = df_f[df_f[col_emp] == empresa_sel]

    # --- CÁLCULO DE PROMEDIOS ---
    colores_config = {2023: WHITE, 2024: LEAF, 2025: CORAL, 2026: SEA}
    anios_activos = sorted(df_f[col_ani].unique())
    
    if anios_activos:
        cols = st.columns(len(anios_activos))
        for i, anio in enumerate(anios_activos):
            with cols[i]:
                # Aquí obtenemos el promedio simple de la columna H, tal cual lo hace tu Excel
                val = df_f[df_f[col_ani] == anio]['Usabilidad_V'].mean()
                
                fig = go.Figure(go.Indicator(
                    mode="gauge+number", value=val*100,
                    number={'suffix': "%", 'valueformat': '.2f', 'font': {'size': 35}},
                    title={'text': f"Promedio {anio}", 'font': {'size': 20}},
                    gauge={'axis': {'range': [0, 100]}, 'bar': {'color': BLACK},
                           'steps': [{'range': [0, 100], 'color': colores_config.get(anio, WHITE)}]}
                ))
                fig.update_layout(height=280, margin=dict(l=20, r=20, t=50, b=20), paper_bgcolor='rgba(0,0,0,0)')
                st.plotly_chart(fig, use_container_width=True, key=f"g_{anio}")

    # --- GRÁFICA DE EVOLUCIÓN ---
    st.subheader("📈 Curva de Engagement")
    if not df_f.empty:
        df_ev = df_f.groupby([col_ani, col_mes])['Usabilidad_V'].mean().reset_index()
        df_ev = df_ev.sort_values([col_ani, col_mes])
        
        fig_l = go.Figure()
        for anio in sorted(anios_sel):
            df_a = df_ev[df_ev[col_ani] == anio]
            if not df_a.empty:
                fig_l.add_trace(go.Scatter(
                    x=[meses_map.get(m) for m in df_a[col_mes]], y=df_a['Usabilidad_V'],
                    name=f"Año {anio}", mode='lines+markers+text',
                    text=[f"{v:.1%}" for v in df_a['Usabilidad_V']], textposition="top center",
                    line=dict(color=colores_config.get(anio, BLACK), width=4)
                ))
        fig_l.update_layout(yaxis=dict(tickformat=".0%", range=[0, 1.1]), height=450, paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)')
        st.plotly_chart(fig_l, use_container_width=True)
else:
    st.error("No se detectaron datos. Verifica que la columna 'Semana' contenga 'Mes total'.")
