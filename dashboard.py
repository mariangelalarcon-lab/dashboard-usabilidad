import streamlit as st
import pandas as pd
import plotly.graph_objects as go

# 1. CONFIGURACIÓN E ICONOS
st.set_page_config(page_title="Holos BI", layout="wide")

LINK_1 = "https://docs.google.com/spreadsheets/d/e/2PACX-1vSWiXR7BLxwzX2wtD_uF59pvxtus8BL5iqgymKSh2-Llwt6smOJzR7ROUxICr57DA/pub?gid=1638907402&single=true&output=csv"
LINK_2 = "https://docs.google.com/spreadsheets/d/e/2PACX-1vSWiXR7BLxwzX2wtD_uF59pvxtus8BL5iqgymKSh2-Llwt6smOJzR7ROUxICr57DA/pub?gid=1341962834&single=true&output=csv"

# Colores Holos
SKY, LEAF, SEA, CORAL, BLACK = "#D1E9F6", "#F1FB8C", "#A9C1F5", "#FF9F86", "#000000"

@st.cache_data(ttl=60)
def load_and_clean():
    try:
        df1 = pd.read_csv(LINK_1)
        df2 = pd.read_csv(LINK_2)
        df = pd.concat([df1, df2], ignore_index=True)
        df.columns = [str(c).strip() for c in df.columns]
        
        # Mapeo robusto de columnas
        c_emp = next((c for c in df.columns if 'Empresa' in c), df.columns[0])
        c_sem = next((c for c in df.columns if 'Semana' in c), "Semana")
        c_usa = next((c for c in df.columns if '%' in c or 'Usabilidad' in c), df.columns[7])
        c_mes = next((c for c in df.columns if 'Mes' in c and 'total' not in c.lower()), "Mes")
        c_ani = next((c for c in df.columns if 'Año' in c or 'Anio' in c), "Año")

        # Limpieza de años (Adiós 1899)
        df['Anio_V'] = pd.to_numeric(df[c_ani], errors='coerce').fillna(0).astype(int)
        df = df[df['Anio_V'] > 2020].copy() 
        
        df['Mes_V'] = pd.to_numeric(df[c_mes], errors='coerce').fillna(0).astype(int)
        df['Empresa_V'] = df[c_emp].astype(str).str.strip()
        df['Semana_V'] = df[c_sem].astype(str).str.strip()

        def to_pct(v):
            try:
                s = str(v).replace('%', '').replace(',', '.').strip()
                n = float(s)
                return n / 100.0 if n > 1.1 else n
            except: return 0.0
        
        df['Valor_V'] = df[c_usa].apply(to_pct)
        return df
    except: return pd.DataFrame()

df = load_and_clean()

if not df.empty:
    # --- SIDEBAR ---
    with st.sidebar:
        st.header("Configuración")
        modo = st.radio("Nivel de Detalle", ["Ejecutivo (Cierres)", "Operativo (Semanal)"])
        
        st.markdown("---")
        emp_list = sorted([e for e in df['Empresa_V'].unique() if e != 'nan'])
        emp_sel = st.selectbox("Seleccionar Empresa", ["Todas las Empresas"] + emp_list)
        
        anios_sel = st.multiselect("Años", sorted(df['Anio_V'].unique(), reverse=True), default=[2025, 2026])
        
        meses_map = {1:'Ene', 2:'Feb', 3:'Mar', 4:'Abr', 5:'May', 6:'Jun', 7:'Jul', 8:'Ago', 9:'Set', 10:'Oct', 11:'Nov', 12:'Dic'}
        meses_sel = st.multiselect("Filtrar Meses", sorted(meses_map.keys()), default=list(meses_map.keys()), format_func=lambda x: meses_map[x])

    # --- FILTRADO LÓGICO ---
    # 1. Filtro base de tiempo
    df_f = df[(df['Anio_V'].isin(anios_sel)) & (df['Mes_V'].isin(meses_sel))].copy()

    # 2. Filtro de Empresa
    if emp_sel != "Todas las Empresas":
        df_f = df_f[df_f['Empresa_V'] == emp_sel]

    # 3. Filtro de Modo (Cierre vs Semanal)
    if modo == "Ejecutivo (Cierres)":
        df_vis = df_f[df_f['Semana_V'].str.contains('total|Total', na=False)]
    else:
        df_vis = df_f[~df_f['Semana_V'].str.contains('total|Total', na=False)]

    # --- CABECERA ---
    st.title(f"📊 Reporte: {emp_sel}")
    st.info(f"Visualizando datos en modo **{modo}** para los meses seleccionados.")

    # --- GAUGES (PROMEDIOS) ---
    anios_act = sorted(df_vis['Anio_V'].unique())
    col_map = {2024: LEAF, 2025: CORAL, 2026: SEA}
    
    if not df_vis.empty:
        cols = st.columns(len(anios_act))
        for i, a in enumerate(anios_act):
            with cols[i]:
                # Cálculo de la media según la selección
                val = df_vis[df_vis['Anio_V'] == a]['Valor_V'].mean()
                
                fig = go.Figure(go.Indicator(
                    mode="gauge+number", value=val*100,
                    number={'suffix': "%", 'valueformat': '.2f'},
                    title={'text': f"Media {a}"},
                    gauge={'axis': {'range': [0, 100]}, 'bar': {'color': BLACK},
                           'steps': [{'range': [0, 100], 'color': col_map.get(a, SKY)}]}
                ))
                fig.update_layout(height=250, margin=dict(l=20,r=20,t=40,b=20))
                st.plotly_chart(fig, use_container_width=True, key=f"g_{a}_{modo}")

    # --- GRÁFICA DE EVOLUCIÓN ---
    st.subheader(f"📈 Curva de Engagement ({modo})")
    
    # Agrupamos por Mes y Semana para que no haya líneas duplicadas
    df_chart = df_vis.groupby(['Anio_V', 'Mes_V', 'Semana_V'])['Valor_V'].mean().reset_index()
    
    fig_l = go.Figure()
    for a in anios_act:
        df_p = df_chart[df_chart['Anio_V'] == a].sort_values(['Mes_V', 'Semana_V'])
        
        # Etiqueta de eje X: Si es mensual solo mes, si es semanal mes + semana
        if modo == "Ejecutivo (Cierres)":
            x_axis = [meses_map.get(m, m) for m in df_p['Mes_V']]
        else:
            x_axis = [f"{meses_map.get(m, m)}-{s[:3]}" for m, s in zip(df_p['Mes_V'], df_p['Semana_V'])]

        fig_l.add_trace(go.Scatter(
            x=x_axis, y=df_p['Valor_V'],
            name=f"Año {a}", mode='lines+markers+text',
            text=[f"{v:.1%}" for v in df_p['Valor_V']], textposition="top center",
            line=dict(color=col_map.get(a, BLACK), width=3)
        ))

    fig_l.update_layout(yaxis=dict(tickformat=".0%", range=[0, 1.1]), height=450)
    st.plotly_chart(fig_l, use_container_width=True)

    # --- TABLA DE AUDITORÍA ---
    with st.expander("🔍 Ver desglose de datos"):
        st.dataframe(df_vis[['Empresa_V', 'Anio_V', 'Mes_V', 'Semana_V', 'Valor_V']])
else:
    st.error("Error al conectar con la base de datos.")
