import streamlit as st
import pandas as pd
import plotly.graph_objects as go

# 1. Configuración de pantalla
st.set_page_config(page_title="Holos | Business Intelligence", layout="wide")

# Enlaces de datos
LINK_1 = "https://docs.google.com/spreadsheets/d/e/2PACX-1vSWiXR7BLxwzX2wtD_uF59pvxtus8BL5iqgymKSh2-Llwt6smOJzR7ROUxICr57DA/pub?gid=1638907402&single=true&output=csv"
LINK_2 = "https://docs.google.com/spreadsheets/d/e/2PACX-1vSWiXR7BLxwzX2wtD_uF59pvxtus8BL5iqgymKSh2-Llwt6smOJzR7ROUxICr57DA/pub?gid=1341962834&single=true&output=csv"

# Paleta Holos
SKY, LEAF, SEA, CORAL, BLACK, WHITE = "#D1E9F6", "#F1FB8C", "#A9C1F5", "#FF9F86", "#000000", "#FFFFFF"

@st.cache_data(ttl=30)
def cargar_data():
    try:
        df1 = pd.read_csv(LINK_1)
        df2 = pd.read_csv(LINK_2)
        df = pd.concat([df1, df2], ignore_index=True)
        df.columns = [str(c).strip() for c in df.columns]
        
        # Identificación flexible de columnas
        c_emp = next((c for c in df.columns if 'Empresa' in c), df.columns[0])
        c_sem = next((c for c in df.columns if 'Semana' in c), None)
        c_colab = next((c for c in df.columns if 'Colaboradores' in c), None)
        c_util = next((c for c in df.columns if 'utilizaron' in c), None)
        c_mes = next((c for c in df.columns if 'Mes' in c and 'total' not in c.lower()), None)
        c_ani = next((c for c in df.columns if 'Año' in c or 'Anio' in c), None)
        c_usa = next((c for c in df.columns if 'Usabilidad' in c or 'Engagement' in c), None)

        def limpiar_num(val):
            try:
                if pd.isna(val): return 0.0
                s = str(val).replace('%', '').replace(',', '.').strip()
                n = float(s)
                return n / 100.0 if n > 1.1 else n
            except: return 0.0

        df['Colab_V'] = pd.to_numeric(df[c_colab], errors='coerce').fillna(0)
        df['Util_V'] = pd.to_numeric(df[c_util], errors='coerce').fillna(0)
        df['Usabilidad_V'] = df[c_usa].apply(limpiar_num)
        df['Anio_V'] = pd.to_numeric(df[c_ani], errors='coerce').fillna(0).astype(int)
        df['Mes_V'] = pd.to_numeric(df[c_mes], errors='coerce').fillna(0).astype(int)
        df['Empresa_V'] = df[c_emp].astype(str).str.strip()
        df['Semana_V'] = df[c_sem].astype(str).str.lower().str.strip() if c_sem else ""
        
        return df, 'Empresa_V', 'Anio_V', 'Mes_V'
    except Exception as e:
        return pd.DataFrame(), str(e), None, None

df, col_emp, col_ani, col_mes = cargar_data()

if not df.empty:
    with st.sidebar:
        st.header("Filtros")
        lista_empresas = sorted([e for e in df[col_emp].unique() if str(e) not in ['nan', 'None']])
        empresa_sel = st.selectbox("Empresa Target", ["Todas las Empresas"] + lista_empresas)
        anios_disp = sorted([a for a in df[col_ani].unique() if a > 2020], reverse=True)
        anios_sel = st.multiselect("Años", anios_disp, default=anios_disp)
        meses_map = {1:'Ene', 2:'Feb', 3:'Mar', 4:'Abr', 5:'May', 6:'Jun', 7:'Jul', 8:'Ago', 9:'Set', 10:'Oct', 11:'Nov', 12:'Dic'}
        meses_sel = st.multiselect("Meses", sorted(meses_map.keys()), default=sorted(meses_map.keys()), format_func=lambda x: meses_map[x])

    st.markdown(f"<h1>📊 Reporte: {empresa_sel}</h1>", unsafe_allow_html=True)

    # --- PROCESAMIENTO DE DATA FILTRADA ---
    df_f = df[(df[col_ani].isin(anios_sel)) & (df[col_mes].isin(meses_sel))].copy()
    
    if empresa_sel != "Todas las Empresas":
        df_f = df_f[df_f[col_emp] == empresa_sel]

    # Función para decidir qué valor mostrar por cada Mes/Empresa
    def obtener_valor_optimo(sub_df):
        # Prioridad 1: Fila que diga "total"
        totales = sub_df[sub_df['Semana_V'].str.contains('total', na=False)]
        if not totales.empty:
            return totales.iloc[-1] # Retorna la última fila de cierre
        # Prioridad 2: Si no hay totales, promedio de lo que haya
        return sub_df.iloc[-1] 

    # Aplicamos la selección de "Mejor Registro"
    df_final = df_f.groupby([col_emp, col_ani, col_mes], group_keys=False).apply(obtener_valor_optimo)

    # --- GAUGES ---
    anios_activos = sorted(df_final[col_ani].unique())
    colores_config = {2024: LEAF, 2025: CORAL, 2026: SEA}
    
    if anios_activos:
        cols = st.columns(len(anios_activos))
        for i, anio in enumerate(anios_activos):
            with cols[i]:
                df_anio = df_final[df_final[col_ani] == anio]
                # Lógica: Suma de usuarios / Suma de colaboradores (Ponderado real)
                u = df_anio['Util_V'].sum()
                c = df_anio['Colab_V'].sum()
                promedio = u / c if c > 0 else 0
                
                fig = go.Figure(go.Indicator(
                    mode="gauge+number", value=promedio*100,
                    number={'suffix': "%", 'valueformat': '.2f', 'font': {'size': 35}},
                    title={'text': f"Promedio {anio}"},
                    gauge={'axis': {'range': [0, 100]}, 'bar': {'color': BLACK},
                           'steps': [{'range': [0, 100], 'color': colores_config.get(anio, WHITE)}]}
                ))
                fig.update_layout(height=280, margin=dict(l=20, r=20, t=50, b=20), paper_bgcolor='rgba(0,0,0,0)')
                st.plotly_chart(fig, use_container_width=True, key=f"g_{anio}")

    # --- GRÁFICA ---
    st.subheader("📈 Curva de Engagement")
    if not df_final.empty:
        df_ev = df_final.groupby([col_ani, col_mes]).apply(
            lambda x: x['Util_V'].sum() / x['Colab_V'].sum() if x['Colab_V'].sum() > 0 else 0
        ).reset_index(name='Val')
        
        fig_l = go.Figure()
        for anio in sorted(anios_sel):
            df_a = df_ev[df_ev[col_ani] == anio].sort_values(col_mes)
            if not df_a.empty:
                fig_l.add_trace(go.Scatter(
                    x=[meses_map.get(m) for m in df_a[col_mes]], y=df_a['Val'],
                    name=f"Año {anio}", mode='lines+markers+text',
                    text=[f"{v:.1%}" for v in df_a['Val']], textposition="top center",
                    line=dict(color=colores_config.get(anio, BLACK), width=3)
                ))
        fig_l.update_layout(yaxis=dict(tickformat=".0%", range=[0, 1.1]), height=400)
        st.plotly_chart(fig_l, use_container_width=True)

    with st.expander("📂 Tabla de Verificación (Data que se está sumando)"):
        st.dataframe(df_final[[col_emp, 'Semana_V', 'Colab_V', 'Util_V', 'Usabilidad_V']])
