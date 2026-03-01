import streamlit as st
import pandas as pd
import plotly.graph_objects as go

# Configuración de página
st.set_page_config(page_title="Holos | Reporte de Cierre", layout="wide")

LINK_1 = "https://docs.google.com/spreadsheets/d/e/2PACX-1vSWiXR7BLxwzX2wtD_uF59pvxtus8BL5iqgymKSh2-Llwt6smOJzR7ROUxICr57DA/pub?gid=1638907402&single=true&output=csv"
LINK_2 = "https://docs.google.com/spreadsheets/d/e/2PACX-1vSWiXR7BLxwzX2wtD_uF59pvxtus8BL5iqgymKSh2-Llwt6smOJzR7ROUxICr57DA/pub?gid=1341962834&single=true&output=csv"

# Colores Holos
SKY, SEA, CORAL, BLACK = "#D1E9F6", "#A9C1F5", "#FF9F86", "#000000"

@st.cache_data(ttl=5)
def cargar_todo():
    try:
        df1 = pd.read_csv(LINK_1)
        df2 = pd.read_csv(LINK_2)
        df = pd.concat([df1, df2], ignore_index=True)
        df.columns = [str(c).strip() for c in df.columns]
        
        # Limpieza robusta de datos numéricos
        def limpiar_usabilidad(x):
            try:
                val = str(x).replace('%', '').replace(',', '.').strip()
                if val == "" or val == "nan": return None
                n = float(val)
                return n/100 if n > 1.1 else n
            except: return None

        res = pd.DataFrame()
        res['Empresa'] = df.iloc[:, 0].astype(str).str.strip()
        res['Semana'] = df.iloc[:, 1].astype(str).str.strip()
        res['Usabilidad'] = df.iloc[:, 7].apply(limpiar_usabilidad)
        res['Mes'] = pd.to_numeric(df.iloc[:, 9], errors='coerce').fillna(0).astype(int)
        res['Anio'] = pd.to_numeric(df.iloc[:, 11], errors='coerce').fillna(0).astype(int)
        
        # IMPORTANTE: Eliminamos lo que sea 0 o nulo para que no baje el promedio
        return res[res['Usabilidad'] > 0]
    except:
        return pd.DataFrame()

df_raw = cargar_todo()

if not df_raw.empty:
    st.sidebar.header("Filtros")
    emp_sel = st.sidebar.selectbox("Empresa", ["Todas las Empresas"] + sorted(df_raw['Empresa'].unique().tolist()))
    
    # Filtrado por Empresa
    df_f = df_raw.copy()
    if emp_sel != "Todas las Empresas":
        df_f = df_f[df_f['Empresa'] == emp_sel]

    st.title(f"📊 Reporte de Engagement: {emp_sel}")

    # --- LÓGICA DE CIERRE MENSUAL ---
    # Aquí forzamos que si no hay "Mes total", use el promedio de las semanas
    def obtener_valor_mes(df_mes):
        totales = df_mes[df_mes['Semana'].str.contains("total", case=False, na=False)]
        if not totales.empty:
            return totales['Usabilidad'].mean() # Prioridad al dato de cierre del Excel
        return df_mes['Usabilidad'].mean() # Si no hay cierre, promedia las semanas

    data_grafico = []
    meses_nombres = {1:'Ene', 2:'Feb', 3:'Mar', 4:'Abr', 5:'May', 6:'Jun', 7:'Jul', 8:'Ago', 9:'Set', 10:'Oct', 11:'Nov', 12:'Dic'}
    
    for anio in [2025, 2026]:
        for mes in range(1, 13):
            df_m = df_f[(df_f['Anio'] == anio) & (df_f['Mes'] == mes)]
            if not df_m.empty:
                valor = obtener_valor_mes(df_m)
                data_grafico.append({'Anio': anio, 'Mes': mes, 'Mes_Nom': meses_nombres[mes], 'Usabilidad': valor})

    df_plot = pd.DataFrame(data_grafico)

    # --- GRÁFICO ---
    fig = go.Figure()
    for a in [2025, 2026]:
        d = df_plot[df_plot['Anio'] == a]
        if not d.empty:
            fig.add_trace(go.Scatter(
                x=d['Mes_Nom'], y=d['Usabilidad'],
                name=f"Año {a}", mode='lines+markers+text',
                text=[f"{v:.1%}" for v in d['Usabilidad']],
                textposition="top center",
                line=dict(width=4, color=SEA if a==2026 else CORAL)
            ))

    fig.update_layout(
        yaxis=dict(tickformat=".0%", range=[0, 1]),
        xaxis=dict(title="Meses 2026"),
        paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)',
        height=500
    )
    st.plotly_chart(fig, use_container_width=True)

    st.success("✅ Sistema actualizado: Febrero ahora se calcula automáticamente basándose en las semanas registradas.")
else:
    st.error("No se detectan datos. Revisa la conexión con Google Sheets.")
