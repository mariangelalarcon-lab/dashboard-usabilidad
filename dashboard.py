import streamlit as st
import pandas as pd
import plotly.graph_objects as go

st.set_page_config(page_title="Holos | Business Intelligence", layout="wide")

# --- DATA LINKS ---
LINK_1 = "https://docs.google.com/spreadsheets/d/e/2PACX-1vSWiXR7BLxwzX2wtD_uF59pvxtus8BL5iqgymKSh2-Llwt6smOJzR7ROUxICr57DA/pub?gid=1638907402&single=true&output=csv"
LINK_2 = "https://docs.google.com/spreadsheets/d/e/2PACX-1vSWiXR7BLxwzX2wtD_uF59pvxtus8BL5iqgymKSh2-Llwt6smOJzR7ROUxICr57DA/pub?gid=1341962834&single=true&output=csv"

# --- PALETA HOLOS ---
SKY, LEAF, SEA, CORAL, BLACK, WHITE = "#D1E9F6", "#F1FB8C", "#A9C1F5", "#FF9F86", "#000000", "#FFFFFF"

@st.cache_data(ttl=30)
def cargar_data():
    try:
        df1 = pd.read_csv(LINK_1)
        df2 = pd.read_csv(LINK_2)
        df = pd.concat([df1, df2], ignore_index=True)
        df.columns = [str(c).strip() for c in df.columns]
        
        # Identificación de columnas basada en tu Excel
        c_emp = next((c for c in df.columns if 'Empresa' in c), df.columns[0])
        c_sem = next((c for c in df.columns if 'Semana' in c), None)
        c_colab = next((c for c in df.columns if 'Colaboradores' in c), None)
        c_util = next((c for c in df.columns if 'utilizaron' in c), None)
        c_mes = next((c for c in df.columns if 'Mes' in c and 'total' not in c.lower()), None)
        c_ani = next((c for c in df.columns if 'Año' in c or 'Anio' in c), None)

        # Limpieza de datos
        df['Colab_V'] = pd.to_numeric(df[c_colab], errors='coerce').fillna(0)
        df['Util_V'] = pd.to_numeric(df[c_util], errors='coerce').fillna(0)
        df['Anio_V'] = pd.to_numeric(df[c_ani], errors='coerce').fillna(0).astype(int)
        df['Mes_V'] = pd.to_numeric(df[c_mes], errors='coerce').fillna(0).astype(int)
        df['Empresa_V'] = df[c_emp].astype(str).str.strip()
        df['Semana_V'] = df[c_sem].astype(str).str.strip() if c_sem else "Mes total"
        
        return df, 'Empresa_V', 'Anio_V', 'Mes_V'
    except Exception as e:
        st.error(f"Error cargando datos: {e}")
        return pd.DataFrame(), None, None, None

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

    st.title(f"📊 Reporte de Usabilidad: {empresa_sel}")

    # --- LÓGICA DE FILTRADO DE JERARQUÍA (ELIMINA EL 19.5%) ---
    # 1. Filtramos por año y mes seleccionados
    df_f = df[(df[col_ani].isin(anios_sel)) & (df[col_mes].isin(meses_sel))].copy()

    # 2. Si hay datos de "Mes total", descartamos las semanas (esto limpia el ruido)
    def filtrar_solo_totales(group):
        if "Mes total" in group['Semana_V'].values:
            return group[group['Semana_V'] == "Mes total"]
        return group

    df_f = df_f.groupby([col_emp, col_ani, col_mes], group_keys=False).apply(filtrar_solo_totales)

    # 3. Filtro de empresa específica si aplica
    if empresa_sel != "Todas las Empresas":
        df_f = df_f[df_f[col_emp] == empresa_sel]

    # --- MÉTRICAS ---
    anios_activos = sorted(df_f[col_ani].unique())
    colores_config = {2024: LEAF, 2025: CORAL, 2026: SEA}
    
    if anios_activos:
        cols = st.columns(len(anios_activos))
        for i, anio in enumerate(anios_activos):
            with cols[i]:
                df_anio = df_f[df_f[col_ani] == anio]
                # Cálculo: Suma de Usuarios / Suma de Colaboradores de los registros finales
                total_util = df_anio['Util_V'].sum()
                total_colab = df_anio['Colab_V'].sum()
                val = total_util / total_colab if total_colab > 0 else 0
                
                fig = go.Figure(go.Indicator(
                    mode="gauge+number", value=val*100,
                    number={'suffix': "%", 'valueformat': '.2f', 'font': {'size': 40}},
                    title={'text': f"Promedio {anio}", 'font': {'size': 20}},
                    gauge={'axis': {'range': [0, 100]}, 'bar': {'color': BLACK},
                           'steps': [{'range': [0, 100], 'color': colores_config.get(anio, WHITE)}]}
                ))
                fig.update_layout(height=280, margin=dict(l=30, r=30, t=50, b=20), paper_bgcolor='rgba(0,0,0,0)')
                st.plotly_chart(fig, use_container_width=True, key=f"gauge_{anio}")

    # --- GRÁFICA ---
    st.subheader("📈 Curva de Engagement")
    if not df_f.empty:
        # Agrupamos por año y mes calculando la división real en cada punto
        df_linea = df_f.groupby([col_ani, col_mes]).apply(
            lambda x: x['Util_V'].sum() / x['Colab_V'].sum() if x['Colab_V'].sum() > 0 else 0
        ).reset_index(name='Val')
        
        fig_l = go.Figure()
        for anio in sorted(anios_sel):
            df_a = df_linea[df_linea[col_ani] == anio].sort_values(col_mes)
            if not df_a.empty:
                fig_l.add_trace(go.Scatter(
                    x=[meses_map.get(m) for m in df_a[col_mes]], y=df_a['Val'],
                    name=f"Año {anio}", mode='lines+markers+text',
                    text=[f"{v:.1%}" for v in df_a['Val']], textposition="top center",
                    line=dict(color=colores_config.get(anio, BLACK), width=4)
                ))
        fig_l.update_layout(yaxis=dict(tickformat=".0%", range=[0, 1.1]), height=450, 
                          paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)')
        st.plotly_chart(fig_l, use_container_width=True)

    with st.expander("🔍 Verificación de datos (Filas utilizadas)"):
        st.write("Estas son las filas que el sistema está sumando para el cálculo actual:")
        st.dataframe(df_f[[col_emp, 'Semana_V', 'Colab_V', 'Util_V']])
