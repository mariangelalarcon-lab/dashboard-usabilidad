import streamlit as st
import pandas as pd
import plotly.graph_objects as go

st.set_page_config(page_title="Holos BI Final", layout="wide")

# Enlaces originales
L1 = "https://docs.google.com/spreadsheets/d/e/2PACX-1vSWiXR7BLxwzX2wtD_uF59pvxtus8BL5iqgymKSh2-Llwt6smOJzR7ROUxICr57DA/pub?gid=1638907402&single=true&output=csv"
L2 = "https://docs.google.com/spreadsheets/d/e/2PACX-1vSWiXR7BLxwzX2wtD_uF59pvxtus8BL5iqgymKSh2-Llwt6smOJzR7ROUxICr57DA/pub?gid=1341962834&single=true&output=csv"

@st.cache_data(ttl=60)
def load_data():
    try:
        df1 = pd.read_csv(L1)
        df2 = pd.read_csv(L2)
        df = pd.concat([df1, df2], ignore_index=True)
        df.columns = [str(c).strip() for c in df.columns]
        
        # Mapeo por palabras clave para no fallar
        col_emp = next((c for c in df.columns if 'Empresa' in c), df.columns[0])
        col_sem = next((c for c in df.columns if 'Semana' in c), df.columns[1])
        col_usa = next((c for c in df.columns if '%' in c or 'Usabilidad' in c), df.columns[7])
        col_mes = next((c for c in df.columns if 'Mes' in c and 'inicio' not in c.lower()), df.columns[8])
        col_ani = next((c for c in df.columns if 'Año' in c or 'Anio' in c), df.columns[11])

        # Limpieza profunda
        df['Anio_V'] = pd.to_numeric(df[col_ani], errors='coerce').fillna(0).astype(int)
        df['Mes_V'] = pd.to_numeric(df[col_mes], errors='coerce').fillna(0).astype(int)
        df['Empresa_V'] = df[col_emp].astype(str).str.strip()
        df['Semana_V'] = df[col_sem].astype(str).str.strip()
        
        def to_f(x):
            try:
                v = str(x).replace('%', '').replace(',', '.').strip()
                return float(v) / 100.0 if float(v) > 1.1 else float(v)
            except: return 0.0
            
        df['Valor_V'] = df[col_usa].apply(to_f)
        
        # Filtro de años para borrar el 1899
        return df[(df['Anio_V'] >= 2024) & (df['Anio_V'] <= 2026)].copy()
    except: return pd.DataFrame()

df = load_data()

if not df.empty:
    with st.sidebar:
        st.header("⚙️ Configuración")
        modo = st.radio("Nivel de Análisis", ["Mensual (Cierres)", "Semanal (Operativo)"])
        empresa = st.selectbox("Seleccionar Empresa", ["Todas las Empresas"] + sorted(df['Empresa_V'].unique()))
        anios = st.multiselect("Años", sorted(df['Anio_V'].unique()), default=[2025, 2026])
        
        meses_map = {1:'Ene', 2:'Feb', 3:'Mar', 4:'Abr', 5:'May', 6:'Jun', 7:'Jul', 8:'Ago', 9:'Set', 10:'Oct', 11:'Nov', 12:'Dic'}
        meses = st.multiselect("Meses", sorted(meses_map.keys()), default=list(meses_map.keys()), format_func=lambda x: meses_map[x])

    # --- FILTRADO ---
    mask = (df['Anio_V'].isin(anios)) & (df['Mes_V'].isin(meses))
    if empresa != "Todas las Empresas":
        mask &= (df['Empresa_V'] == empresa)
    
    df_f = df[mask].copy()
    
    # Separación por modo
    if modo == "Mensual (Cierres)":
        df_vis = df_f[df_f['Semana_V'].str.contains('total|Total', na=False)]
    else:
        df_vis = df_f[~df_f['Semana_V'].str.contains('total|Total', na=False)]

    # --- UI ---
    st.title(f"📊 Reporte: {empresa}")
    
    if not df_vis.empty:
        # Gauges
        anios_list = sorted(df_vis['Anio_V'].unique())
        cols = st.columns(len(anios_list))
        for i, a in enumerate(anios_list):
            val = df_vis[df_vis['Anio_V'] == a]['Valor_V'].mean()
            with cols[i]:
                st.metric(f"Media {a}", f"{val:.2%}")
                # Mini Gauge simple
                fig_g = go.Figure(go.Indicator(
                    mode="gauge+number", value=val*100,
                    gauge={'axis':{'range':[0,100]}, 'bar':{'color':'black'}}
                ))
                fig_g.update_layout(height=150, margin=dict(l=10,r=10,t=10,b=10))
                st.plotly_chart(fig_g, use_container_width=True)

        # Gráfica
        st.subheader("📈 Curva de Engagement")
        df_chart = df_vis.groupby(['Anio_V', 'Mes_V', 'Semana_V'])['Valor_V'].mean().reset_index()
        fig = go.Figure()
        for a in anios_list:
            d = df_chart[df_chart['Anio_V'] == a].sort_values(['Mes_V'])
            x = [f"{meses_map.get(m)}-{s[:3]}" for m, s in zip(d['Mes_V'], d['Semana_V'])]
            fig.add_trace(go.Scatter(x=x, y=d['Valor_V'], name=f"Año {a}", mode='lines+markers'))
        
        fig.update_layout(yaxis=dict(tickformat=".1%"), height=400)
        st.plotly_chart(fig, use_container_width=True)
    else:
        st.warning("No hay datos para la combinación seleccionada. Prueba cambiando el Año o el Mes.")
        
    # Tabla de Validación
    with st.expander("🔍 Auditoría de datos (Compara con tu Excel)"):
        st.dataframe(df_vis[['Empresa_V', 'Semana_V', 'Valor_V', 'Anio_V']].sort_values('Anio_V'))
