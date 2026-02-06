import streamlit as st
import pandas as pd
import plotly.graph_objects as go

# 1. Configuración de pantalla
st.set_page_config(page_title="Holos | BI", layout="wide")

# Enlaces de datos
LINK_1 = "https://docs.google.com/spreadsheets/d/e/2PACX-1vSWiXR7BLxwzX2wtD_uF59pvxtus8BL5iqgymKSh2-Llwt6smOJzR7ROUxICr57DA/pub?gid=1638907402&single=true&output=csv"
LINK_2 = "https://docs.google.com/spreadsheets/d/e/2PACX-1vSWiXR7BLxwzX2wtD_uF59pvxtus8BL5iqgymKSh2-Llwt6smOJzR7ROUxICr57DA/pub?gid=1341962834&single=true&output=csv"

@st.cache_data(ttl=60)
def cargar_limpiar_data():
    try:
        df1 = pd.read_csv(LINK_1)
        df2 = pd.read_csv(LINK_2)
        df = pd.concat([df1, df2], ignore_index=True)
        df.columns = [str(c).strip() for c in df.columns]
        
        # Identificar columnas
        c_emp = next((c for c in df.columns if 'Empresa' in c), "Nombre de la Empresa")
        c_sem = next((c for c in df.columns if 'Semana' in c), "Semana")
        c_usa = next((c for c in df.columns if '%' in c or 'Usabilidad' in c), df.columns[7])
        c_mes = next((c for c in df.columns if 'Mes' in c and 'total' not in c.lower()), "Mes")
        c_ani = next((c for c in df.columns if 'Año' in c or 'Anio' in c), "Año")

        # Limpiar números y Años (Elimina el 1899)
        df['Anio_V'] = pd.to_numeric(df[c_ani], errors='coerce').fillna(0).astype(int)
        df = df[df['Anio_V'] > 2020] # <--- FILTRO CRÍTICO PARA ELIMINAR 1899
        
        df['Mes_V'] = pd.to_numeric(df[c_mes], errors='coerce').fillna(0).astype(int)
        df['Empresa_V'] = df[c_emp].astype(str).str.strip()
        df['Semana_V'] = df[c_sem].astype(str).str.strip()

        def parse_pct(val):
            try:
                s = str(val).replace('%', '').replace(',', '.').strip()
                n = float(s)
                return n / 100.0 if n > 1.1 else n
            except: return 0.0
        
        df['Val_V'] = df[c_usa].apply(parse_pct)
        return df
    except: return pd.DataFrame()

df = cargar_limpiar_data()

if not df.empty:
    with st.sidebar:
        st.header("Configuración")
        modo = st.radio("Ver datos como:", ["Ejecutivo (Cierres)", "Operativo (Semanal)"])
        empresa_sel = st.selectbox("Empresa", ["Todas las Empresas"] + sorted(df['Empresa_V'].unique()))
        anios_disp = sorted(df['Anio_V'].unique(), reverse=True)
        anios_sel = st.multiselect("Años", anios_disp, default=[2025, 2026])
        
    # --- FILTRADO ---
    df_f = df[df['Anio_V'].isin(anios_sel)].copy()
    
    if modo == "Ejecutivo (Cierres)":
        df_f = df_f[df_f['Semana_V'].str.contains('total|Total', na=False)]
    else:
        df_f = df_f[~df_f['Semana_V'].str.contains('total|Total', na=False)]

    if empresa_sel != "Todas las Empresas":
        df_f = df_f[df_f['Empresa_V'] == empresa_sel]

    # --- TITULO Y GAUGES ---
    st.title(f"📊 {empresa_sel}")
    st.caption(f"Visualización: {modo}")

    anios_activos = sorted(df_f['Anio_V'].unique())
    if anios_activos:
        cols = st.columns(len(anios_activos))
        for i, a in enumerate(anios_activos):
            df_anio = df_f[df_f['Anio_V'] == a]
            # Si es Natura, toma Natura. Si es Todas, toma el promedio del Excel (32.72%)
            valor = df_anio['Val_V'].mean()
            with cols[i]:
                st.metric(f"Promedio {a}", f"{valor:.2%}")

    # --- GRÁFICA CORREGIDA (Sin telarañas) ---
    st.subheader("📈 Curva de Engagement")
    
    # Agrupamos para que solo haya UNA línea por año
    df_chart = df_f.groupby(['Anio_V', 'Mes_V', 'Semana_V'])['Val_V'].mean().reset_index()
    
    fig = go.Figure()
    colors = {2024: "#F1FB8C", 2025: "#FF9F86", 2026: "#A9C1F5"}
    meses_n = {1:'Ene', 2:'Feb', 3:'Mar', 4:'Abr', 5:'May', 6:'Jun', 7:'Jul', 8:'Ago', 9:'Set', 10:'Oct', 11:'Nov', 12:'Dic'}

    for a in anios_activos:
        df_p = df_chart[df_chart['Anio_V'] == a].sort_values(['Mes_V', 'Semana_V'])
        # Eje X limpio: Mes + Semana
        x_labels = [f"{meses_n.get(m, m)} - {s}" for m, s in zip(df_p['Mes_V'], df_p['Semana_V'])]
        
        fig.add_trace(go.Scatter(
            x=x_labels, y=df_p['Val_V'], name=str(a),
            mode='lines+markers', line=dict(width=3, color=colors.get(a, "#000"))
        ))

    fig.update_layout(yaxis=dict(tickformat=".0%", range=[0, 1.1]), height=400, margin=dict(l=0,r=0,b=0,t=30))
    st.plotly_chart(fig, use_container_width=True)

    # --- TABLA DE VERDAD ---
    with st.expander("🔍 Ver datos exactos de esta tabla"):
        st.dataframe(df_f[['Empresa_V', 'Anio_V', 'Semana_V', 'Val_V']].sort_values(['Anio_V', 'Semana_V']))

else:
    st.error("No se detectan datos. Revisa la conexión con el Excel.")
