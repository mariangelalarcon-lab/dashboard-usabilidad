import streamlit as st
import pandas as pd
import plotly.graph_objects as go

# Configuración básica
st.set_page_config(page_title="Holos BI", layout="wide")

# Enlaces
LINK_1 = "https://docs.google.com/spreadsheets/d/e/2PACX-1vSWiXR7BLxwzX2wtD_uF59pvxtus8BL5iqgymKSh2-Llwt6smOJzR7ROUxICr57DA/pub?gid=1638907402&single=true&output=csv"
LINK_2 = "https://docs.google.com/spreadsheets/d/e/2PACX-1vSWiXR7BLxwzX2wtD_uF59pvxtus8BL5iqgymKSh2-Llwt6smOJzR7ROUxICr57DA/pub?gid=1341962834&single=true&output=csv"

# Colores
SKY, LEAF, SEA, CORAL, BLACK = "#D1E9F6", "#F1FB8C", "#A9C1F5", "#FF9F86", "#000000"

@st.cache_data(ttl=60)
def load_data():
    try:
        df1 = pd.read_csv(LINK_1)
        df2 = pd.read_csv(LINK_2)
        df = pd.concat([df1, df2], ignore_index=True)
        df.columns = [str(c).strip() for c in df.columns]
        
        # Mapeo de columnas esenciales
        c_emp = next((c for c in df.columns if 'Empresa' in c), df.columns[0])
        c_col = next((c for c in df.columns if 'Colaboradores' in c), None)
        c_uti = next((c for c in df.columns if 'utilizaron' in c), None)
        c_mes = next((c for c in df.columns if 'Mes' in c and 'total' not in c.lower()), None)
        c_ani = next((c for c in df.columns if 'Año' in c or 'Anio' in c), None)

        # Convertir a números
        df['Colab'] = pd.to_numeric(df[c_col], errors='coerce').fillna(0)
        df['Util'] = pd.to_numeric(df[c_uti], errors='coerce').fillna(0)
        df['Anio'] = pd.to_numeric(df[c_ani], errors='coerce').fillna(0).astype(int)
        df['Mes'] = pd.to_numeric(df[c_mes], errors='coerce').fillna(0).astype(int)
        df['Empresa'] = df[c_emp].astype(str).str.strip()
        
        return df
    except:
        return pd.DataFrame()

df = load_data()

if not df.empty:
    # --- Sidebar ---
    with st.sidebar:
        st.header("Filtros")
        empresas = sorted(df['Empresa'].unique())
        emp_sel = st.selectbox("Seleccionar Empresa", ["Todas las Empresas"] + empresas)
        anios = sorted(df['Anio'].unique(), reverse=True)
        anios_sel = st.multiselect("Años", anios, default=[2025, 2026])
        meses_map = {1:'Ene', 2:'Feb', 3:'Mar', 4:'Abr', 5:'May', 6:'Jun', 7:'Jul', 8:'Ago', 9:'Set', 10:'Oct', 11:'Nov', 12:'Dic'}
        meses_sel = st.multiselect("Meses", sorted(meses_map.keys()), default=list(meses_map.keys()), format_func=lambda x: meses_map[x])

    st.title(f"Reporte: {emp_sel}")

    # Filtrado base
    df_f = df[(df['Anio'].isin(anios_sel)) & (df['Mes'].isin(meses_sel))]
    if emp_sel != "Todas las Empresas":
        df_f = df_f[df_f['Empresa'] == emp_sel]

    # --- Gauges ---
    color_map = {2024: LEAF, 2025: CORAL, 2026: SEA}
    actual_anios = sorted(df_f['Anio'].unique())
    
    if actual_anios:
        cols = st.columns(len(actual_anios))
        for i, a in enumerate(actual_anios):
            with cols[i]:
                df_a = df_f[df_f['Anio'] == a]
                # CÁLCULO REAL: Usuarios / Colaboradores
                total_u = df_a['Util'].sum()
                total_c = df_a['Colab'].sum()
                val = (total_u / total_c * 100) if total_c > 0 else 0
                
                fig = go.Figure(go.Indicator(
                    mode="gauge+number", value=val,
                    number={'suffix': "%", 'valueformat': '.1f'},
                    title={'text': f"Media {a}"},
                    gauge={'axis': {'range': [0, 100]}, 'bar': {'color': BLACK},
                           'steps': [{'range': [0, 100], 'color': color_map.get(a, SKY)}]}
                ))
                fig.update_layout(height=250, margin=dict(l=20,r=20,t=40,b=20))
                st.plotly_chart(fig, use_container_width=True)

    # --- Gráfica de Líneas ---
    st.subheader("Curva de Engagement")
    # Agrupamos por año y mes para la línea
    df_linea = df_f.groupby(['Anio', 'Mes']).apply(
        lambda x: (x['Util'].sum() / x['Colab'].sum() * 100) if x['Colab'].sum() > 0 else 0
    ).reset_index(name='Val')

    fig_line = go.Figure()
    for a in actual_anios:
        df_plot = df_linea[df_linea['Anio'] == a].sort_values('Mes')
        fig_line.add_trace(go.Scatter(
            x=[meses_map[m] for m in df_plot['Mes']], 
            y=df_plot['Val'],
            name=f"Año {a}",
            mode='lines+markers',
            line=dict(color=color_map.get(a, BLACK), width=3)
        ))
    
    fig_line.update_layout(yaxis_range=[0, 105], height=400)
    st.plotly_chart(fig_line, use_container_width=True)

    # Tabla de comprobación (Opcional, para que veas que los datos están ahí)
    with st.expander("Ver detalle de datos"):
        st.dataframe(df_f[['Empresa', 'Anio', 'Mes', 'Colab', 'Util']])
