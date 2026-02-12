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
        
        res = pd.DataFrame()
        res['Empresa'] = df.iloc[:, 0].astype(str).str.strip()
        res['Semana_Texto'] = df.iloc[:, 1].astype(str).str.strip()
        res['Semana_Lower'] = res['Semana_Texto'].str.lower()
        
        def limpiar_p(x):
            try:
                v = float(str(x).replace('%','').replace(',','.'))
                return v/100 if v > 1.1 else v
            except: return 0.0
            
        res['Usabilidad'] = df.iloc[:, 7].apply(limpiar_p)
        res['Mes'] = pd.to_numeric(df.iloc[:, 9], errors='coerce').fillna(0).astype(int)
        res['Anio'] = pd.to_numeric(df.iloc[:, 11], errors='coerce').fillna(0).astype(int)
        
        return res[res['Anio'] >= 2025]
    except:
        return pd.DataFrame()

df = cargar_data()

if not df.empty:
    with st.sidebar:
        st.header("⚡ Panel de Control")
        interfaz = st.radio("Ver Reporte:", ["Resumen Ejecutivo (Totales)", "Reporte Operativo (Semanas)"])
        
        empresa_sel = st.selectbox("Empresa:", ["Todas las Empresas"] + sorted(df['Empresa'].unique().tolist()))
        anios_sel = st.multiselect("Años:", [2026, 2025], default=[2026, 2025])
        
        # Diccionario para evitar el TypeError anterior
        meses_nombres = {1:'Ene', 2:'Feb', 3:'Mar', 4:'Abr', 5:'May', 6:'Jun', 7:'Jul', 8:'Ago', 9:'Sep', 10:'Oct', 11:'Nov', 12:'Dic'}
        meses_sel = st.multiselect("Meses:", list(meses_nombres.keys()), default=[1, 2], 
                                   format_func=lambda x: meses_nombres.get(x, x))

    # FILTRO CORREGIDO (Sin SyntaxError)
    mask = (df['Anio'].isin(anios_sel)) & (df['Mes'].isin(meses_sel))
    if empresa_sel != "Todas las Empresas":
        mask &= (df['Empresa'] == empresa_sel)
    
    df_filtrado = df[mask].copy()

    if "Ejecutivo" in interfaz:
        st.title("📊 Resumen Ejecutivo")
        # Filtra solo las filas que dicen "total"
        df_vis = df_filtrado[df_filtrado['Semana_Lower'].str.contains('total', na=False)]
        label_x = 'Mes'
        sort_by = ['Anio', 'Mes']
    else:
        st.title("📉 Reporte Operativo Semanal")
        # Excluye las filas de totales
        df_vis = df_filtrado[~df_filtrado['Semana_Lower'].str.contains('total', na=False)]
        orden_sem = {'1era semana':1, '2da semana':2, '3era semana':3, '4ta semana':4}
        df_vis['rank'] = df_vis['Semana_Lower'].map(orden_sem).fillna(5)
        label_x = 'Semana_Texto'
        sort_by = ['Anio', 'Mes', 'rank']

    if not df_vis.empty:
        df_final = df_vis.groupby(['Anio', 'Mes', label_x] + (['rank'] if "Operativo" in interfaz else [])).agg({'Usabilidad':'mean'}).reset_index()
        df_final = df_final.sort_values(sort_by)
        
        # Etiqueta para el eje X
        df_final['Eje_X'] = df_final.apply(lambda x: f"{meses_nombres.get(x['Mes'])}-{x[label_x]}", axis=1)

        fig = go.Figure()
        colores = {2025: "#FF9F86", 2026: "#A9C1F5"}

        for a in sorted(anios_sel):
            d = df_final[df_final['Anio'] == a]
            if not d.empty:
                fig.add_trace(go.Scatter(
                    x=d['Eje_X'], y=d['Usabilidad'],
                    name=f"Año {a}", mode='lines+markers+text',
                    text=[f"{v:.1%}" for v in d['Usabilidad']],
                    textposition="top center",
                    line=dict(color=colores.get(a, "#000000"), width=4),
                    connectgaps=True
                ))

        fig.update_layout(yaxis=dict(tickformat=".0%", range=[0, 1.1]), hovermode="x unified", height=500)
        st.plotly_chart(fig, use_container_width=True)
    else:
        st.info("No hay datos para mostrar. Selecciona meses o empresas que tengan información en el Excel.")

else:
    st.error("Error de conexión. Verifica que el Google Sheet esté publicado como CSV.")
