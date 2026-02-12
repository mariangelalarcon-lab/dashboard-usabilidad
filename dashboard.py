import streamlit as st
import pandas as pd
import plotly.graph_objects as go

# 1. Configuración de Marca
st.set_page_config(page_title="Holos BI", layout="wide")

LINK_1 = "https://docs.google.com/spreadsheets/d/e/2PACX-1vSWiXR7BLxwzX2wtD_uF59pvxtus8BL5iqgymKSh2-Llwt6smOJzR7ROUxICr57DA/pub?gid=1638907402&single=true&output=csv"
LINK_2 = "https://docs.google.com/spreadsheets/d/e/2PACX-1vSWiXR7BLxwzX2wtD_uF59pvxtus8BL5iqgymKSh2-Llwt6smOJzR7ROUxICr57DA/pub?gid=1341962834&single=true&output=csv"

@st.cache_data(ttl=5)
def cargar_data():
    try:
        df = pd.concat([pd.read_csv(LINK_1), pd.read_csv(LINK_2)], ignore_index=True)
        df.columns = [str(c).strip() for c in df.columns]
        
        # Procesamiento de columnas críticas
        res = pd.DataFrame()
        res['Empresa'] = df.iloc[:, 0].astype(str).str.strip()
        res['Semana_Texto'] = df.iloc[:, 1].astype(str).str.strip()
        res['Semana_Lower'] = res['Semana_Texto'].str.lower()
        
        # Limpieza de Porcentaje
        def limpiar(x):
            try:
                val = float(str(x).replace('%','').replace(',','.'))
                return val/100 if val > 1.1 else val
            except: return 0.0
            
        res['Usabilidad'] = df.iloc[:, 7].apply(limpiar)
        res['Mes'] = pd.to_numeric(df.iloc[:, 9], errors='coerce').fillna(0).astype(int)
        res['Anio'] = pd.to_numeric(df.iloc[:, 11], errors='coerce').fillna(0).astype(int)
        
        return res[res['Anio'] >= 2025]
    except:
        return pd.DataFrame()

df = cargar_data()

if not df.empty:
    # --- BARRA LATERAL ---
    with st.sidebar:
        st.header("⚡ Panel de Control")
        interfaz = st.radio("Ver Reporte:", ["Resumen Ejecutivo (Totales)", "Reporte Operativo (Semanas)"])
        
        empresa_sel = st.selectbox("Empresa:", ["Todas las Empresas"] + sorted(df['Empresa'].unique().tolist()))
        anios_sel = st.multiselect("Años:", [2026, 2025], default=[2026, 2025])
        
        # Selección de meses sin funciones lambda complejas para evitar el TypeError
        meses_nombres = {1:'Ene', 2:'Feb', 3:'Mar', 4:'Abr', 5:'May', 6:'Jun', 7:'Jul', 8:'Ago', 9:'Sep', 10:'Oct', 11:'Nov', 12:'Dic'}
        meses_sel = st.multiselect("Meses:", list(meses_nombres.keys()), default=[1, 2], 
                                   format_func=lambda x: meses_nombres.get(x))

    # Filtrado Base
    mask = (df['Anio.isin(anios_sel)) & (df['Mes'].isin(meses_sel))
    if empresa_sel != "Todas las Empresas":
        mask &= (df['Empresa'] == empresa_sel)
    
    df_filtrado = df[mask].copy()

    # --- LÓGICA DE INTERFACES ---
    if "Ejecutivo" in interfaz:
        st.title("📊 Resumen Ejecutivo")
        st.markdown("Mostrando únicamente el cierre de cada mes (**Mes total**).")
        # Solo filas que contengan 'total'
        df_vis = df_filtrado[df_filtrado['Semana_Lower'].str.contains('total', na=False)]
        label_x = 'Mes'
    else:
        st.title("📉 Reporte Operativo Semanal")
        st.markdown("Progreso detallado semana a semana.")
        # Excluir los totales para ver el avance real
        df_vis = df_filtrado[~df_filtrado['Semana_Lower'].str.contains('total', na=False)]
        
        # Ordenar semanas
        orden_sem = {'1era semana':1, '2da semana':2, '3era semana':3, '4ta semana':4}
        df_vis['rank'] = df_vis['Semana_Lower'].map(orden_sem).fillna(5)
        df_vis = df_vis.sort_values(['Anio', 'Mes', 'rank'])
        label_x = 'Semana_Texto'

    if not df_vis.empty:
        # Agrupar para promediar empresas
        df_final = df_vis.groupby(['Anio', 'Mes', label_x])['Usabilidad'].mean().reset_index()
        
        # Crear etiquetas de eje X: "Ene-1era Semana"
        df_final['Etiqueta'] = df_final.apply(lambda x: f"{meses_nombres.get(x['Mes'])}-{x[label_x]}", axis=1)

        # Gráfica Pro
        fig = go.Figure()
        colores = {2025: "#FF9F86", 2026: "#A9C1F5"}

        for a in sorted(anios_sel):
            d = df_final[df_final['Anio'] == a]
            if not d.empty:
                fig.add_trace(go.Scatter(
                    x=d['Etiqueta'], y=d['Usabilidad'],
                    name=f"Año {a}", mode='lines+markers+text',
                    text=[f"{v:.1%}" for v in d['Usabilidad']],
                    textposition="top center",
                    line=dict(color=colores.get(a, "#000000"), width=4)
                ))

        fig.update_layout(yaxis=dict(tickformat=".0%", range=[0, 1.1]), hovermode="x unified", height=500)
        st.plotly_chart(fig, use_container_width=True)
    else:
        st.info("No hay datos para mostrar con los filtros seleccionados.")

else:
    st.error("Esperando conexión con Google Sheets. Revisa que el archivo esté publicado.")
