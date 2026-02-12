import streamlit as st
import pandas as pd
import plotly.graph_objects as go

# 1. Configuración de Marca y Estilo
st.set_page_config(page_title="Holos BI | Usability Dashboard", layout="wide")

LINK_1 = "https://docs.google.com/spreadsheets/d/e/2PACX-1vSWiXR7BLxwzX2wtD_uF59pvxtus8BL5iqgymKSh2-Llwt6smOJzR7ROUxICr57DA/pub?gid=1638907402&single=true&output=csv"
LINK_2 = "https://docs.google.com/spreadsheets/d/e/2PACX-1vSWiXR7BLxwzX2wtD_uF59pvxtus8BL5iqgymKSh2-Llwt6smOJzR7ROUxICr57DA/pub?gid=1341962834&single=true&output=csv"

# Paleta de colores Pro
SKY, LEAF, SEA, CORAL, BLACK = "#D1E9F6", "#F1FB8C", "#A9C1F5", "#FF9F86", "#000000"

@st.cache_data(ttl=5)
def cargar_limpiar_data():
    try:
        df = pd.concat([pd.read_csv(LINK_1), pd.read_csv(LINK_2)], ignore_index=True)
        df.columns = [str(c).strip() for c in df.columns]
        
        # Mapeo posicional blindado
        temp_df = pd.DataFrame()
        temp_df['Empresa'] = df.iloc[:, 0].astype(str).str.strip()
        temp_df['Semana_Raw'] = df.iloc[:, 1].astype(str).str.strip()
        temp_df['Semana_Clean'] = temp_df['Semana_Raw'].str.lower()
        temp_df['Usabilidad'] = pd.to_numeric(df.iloc[:, 7].astype(str).str.replace('%','').str.replace(',','.'), errors='coerce').fillna(0)
        # Ajuste de escala: si es mayor a 1, asumimos que es porcentaje entero (ej. 34.5)
        temp_df['Usabilidad'] = temp_df['Usabilidad'].apply(lambda x: x/100 if x > 1.1 else x)
        
        temp_df['Mes_N'] = pd.to_numeric(df.iloc[:, 9], errors='coerce').fillna(0).astype(int)
        temp_df['Anio_N'] = pd.to_numeric(df.iloc[:, 11], errors='coerce').fillna(0).astype(int)
        
        # Filtro de filas válidas
        return temp_df[(temp_df['Anio_N'] >= 2025) & (temp_df['Empresa'] != 'nan')]
    except Exception as e:
        st.error(f"Error de conexión: {e}")
        return pd.DataFrame()

df = cargar_limpiar_data()

if not df.empty:
    # --- INTERFAZ DE FILTROS ---
    with st.sidebar:
        st.header("⚡ Panel de Control")
        tipo_reporte = st.radio("Selecciona Interfaz:", ["Resumen Ejecutivo (Cierres)", "Reporte Operativo (Semanal)"])
        
        st.divider()
        empresa_list = sorted([e for e in df['Empresa'].unique() if e != 'nan'])
        empresa_sel = st.selectbox("Empresa Target", ["Todas las Empresas"] + empresa_list)
        
        anios_sel = st.multiselect("Años", sorted(df['Anio_N'].unique(), reverse=True), default=[2026, 2025])
        meses_sel = st.multiselect("Meses", [1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12], 
                                   default=[1, 2], format_func=lambda x: {1:'Ene', 2:'Feb', 3:'Mar'}.get(x, x))

    # Filtrado base
    df_f = df[(df['Anio_N'].isin(anios_sel)) & (df['Mes_N'].isin(meses_sel))].copy()
    if empresa_sel != "Todas las Empresas":
        df_f = df_f[df_f['Empresa'] == empresa_sel]

    # --- LÓGICA DE INTERFACES ---
    if "Ejecutivo" in tipo_reporte:
        st.title("📊 Resumen Ejecutivo: Cierres Mensuales")
        df_plot = df_f[df_f['Semana_Clean'].str.contains('total', na=False)]
        x_col = 'Mes_N'
        sort_cols = ['Anio_N', 'Mes_N']
    else:
        st.title("📉 Reporte Operativo: Progreso Semanal")
        df_plot = df_f[~df_f['Semana_Clean'].str.contains('total', na=False)]
        # Asignar orden a semanas
        sem_order = {'1era semana':1, '2da semana':2, '3era semana':3, '4ta semana':4}
        df_plot['sem_rank'] = df_plot['Semana_Clean'].map(sem_order).fillna(5)
        x_col = 'Semana_Raw'
        sort_cols = ['Anio_N', 'Mes_N', 'sem_rank']

    if not df_plot.empty:
        # Agrupar para promediar si hay múltiples empresas seleccionadas
        df_final = df_plot.groupby(['Anio_N', 'Mes_N', x_col] + ([ 'sem_rank'] if "Operativo" in tipo_reporte else [])).agg({'Usabilidad':'mean'}).reset_index()
        df_final = df_final.sort_values(sort_cols)

        # Crear etiquetas de eje X: "Ene-Total" o "Feb-1era Semana"
        mes_map = {1:'Ene', 2:'Feb', 3:'Mar', 4:'Abr', 5:'May', 6:'Jun'}
        df_final['Eje_X'] = df_final.apply(lambda r: f"{mes_map.get(r['Mes_N'], r['Mes_N'])}-{r[x_col]}", axis=1)

        # --- GRÁFICA ---
        fig = go.Figure()
        colors = {2025: CORAL, 2026: SEA}

        for anio in sorted(anios_sel):
            curr_df = df_final[df_final['Anio_N'] == anio]
            if not curr_df.empty:
                fig.add_trace(go.Scatter(
                    x=curr_df['Eje_X'], 
                    y=curr_df['Usabilidad'],
                    name=f"Año {anio}",
                    mode='lines+markers+text',
                    text=[f"{v:.1%}" for v in curr_df['Usabilidad']],
                    textposition="top center",
                    line=dict(color=colors.get(anio, BLACK), width=4 if anio==2026 else 2),
                    connectgaps=True
                ))

        fig.update_layout(
            yaxis=dict(tickformat=".0%", range=[0, 1.1], gridcolor="#eeeeee"),
            xaxis=dict(gridcolor="#eeeeee"),
            plot_bgcolor="white",
            hovermode="x unified",
            height=500
        )
        st.plotly_chart(fig, use_container_width=True)

        # --- SECCIÓN DE AUDITORÍA (Oculta por defecto) ---
        with st.expander("🔍 Verificador de Registros (Evita el KeyError)"):
            st.write(f"Mostrando {len(df_plot)} filas encontradas:")
            st.dataframe(df_plot[['Empresa', 'Anio_N', 'Mes_N', 'Semana_Raw', 'Usabilidad']])
    else:
        st.info("No se encontraron datos para los filtros seleccionados. Verifica que el Mes y Año coincidan en el Excel.")

else:
    st.error("No se pudo conectar con el Google Sheet. Verifica los enlaces de publicación CSV.")
