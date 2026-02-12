import streamlit as st
import pandas as pd
import plotly.graph_objects as go

# 1. Configuración de pantalla
st.set_page_config(page_title="Holos | Business Intelligence", layout="wide")

LINK_1 = "https://docs.google.com/spreadsheets/d/e/2PACX-1vSWiXR7BLxwzX2wtD_uF59pvxtus8BL5iqgymKSh2-Llwt6smOJzR7ROUxICr57DA/pub?gid=1638907402&single=true&output=csv"
LINK_2 = "https://docs.google.com/spreadsheets/d/e/2PACX-1vSWiXR7BLxwzX2wtD_uF59pvxtus8BL5iqgymKSh2-Llwt6smOJzR7ROUxICr57DA/pub?gid=1341962834&single=true&output=csv"

SKY, LEAF, SEA, CORAL, BLACK = "#D1E9F6", "#F1FB8C", "#A9C1F5", "#FF9F86", "#000000"

@st.cache_data(ttl=5)
def cargar_unificado():
    try:
        df1 = pd.read_csv(LINK_1)
        df2 = pd.read_csv(LINK_2)
        df = pd.concat([df1, df2], ignore_index=True)
        df.columns = [str(c).strip() for c in df.columns]
        
        res = pd.DataFrame()
        res['Empresa'] = df.iloc[:, 0].astype(str).str.strip()
        res['Semana'] = df.iloc[:, 1].astype(str).str.strip()
        
        def clean_num(x):
            try:
                txt = str(x).replace('%', '').replace(',', '.').strip()
                if txt == "" or txt == "nan": return None
                v = float(txt)
                return v/100 if v > 1.1 else v
            except: return None

        res['Usabilidad'] = df.iloc[:, 7].apply(clean_num)
        res['Mes'] = pd.to_numeric(df.iloc[:, 9], errors='coerce').fillna(0).astype(int)
        res['Anio'] = pd.to_numeric(df.iloc[:, 11], errors='coerce').fillna(0).astype(int)
        
        # Filtramos valores nulos o ceros que ensucian el promedio del "Mes Total"
        return res[res['Usabilidad'] > 0.0001] 
    except:
        return pd.DataFrame()

df_total = cargar_unificado()

if not df_total.empty:
    with st.sidebar:
        st.header("🎛️ Filtros")
        empresa_sel = st.selectbox("Empresa", ["Todas las Empresas"] + sorted(df_total['Empresa'].unique().tolist()))
        anios_sel = st.multiselect("Años", [2026, 2025], default=[2026, 2025])
        mes_nom = {1:'Ene', 2:'Feb', 3:'Mar'}
        meses_sel = st.multiselect("Meses", [1, 2], default=[1, 2], format_func=lambda x: mes_nom.get(x))

    st.markdown(f"<h1>📊 Dashboard de Usabilidad: {empresa_sel}</h1>", unsafe_allow_html=True)

    # FILTRO CORREGIDO (Sin error de comillas)
    mask = (df_total['Anio'].isin(anios_sel)) & (df_total['Mes'].isin(meses_sel))
    if empresa_sel != "Todas las Empresas":
        mask &= (df_total['Empresa'] == empresa_sel)
    df_f = df_total[mask].copy()

    # --- GRÁFICO DE AVANCE ---
    def rankear(s):
        s = s.lower()
        if '1era' in s: return 1
        if '2da' in s: return 2
        if '3era' in s: return 3
        if '4ta' in s: return 4
        return 5

    df_f['Orden'] = df_f['Semana'].apply(rankear)
    df_plot = df_f.groupby(['Anio', 'Mes', 'Semana', 'Orden'])['Usabilidad'].mean().reset_index()
    df_plot = df_plot.sort_values(['Anio', 'Mes', 'Orden'])

    fig_l = go.Figure()
    for a in sorted(anios_sel):
        d = df_plot[df_plot['Anio'] == a]
        if not d.empty:
            etiquetas = [f"{mes_nom.get(m)} - {s}" for m, s in zip(d['Mes'], d['Semana'])]
            fig_l.add_trace(go.Scatter(
                x=etiquetas, y=d['Usabilidad'],
                name=f"Año {a}", mode='lines+markers+text',
                text=[f"{v:.1%}" for v in d['Usabilidad']],
                textposition="top center",
                line=dict(width=4, color=SEA if a==2026 else CORAL),
                connectgaps=True
            ))

    fig_l.update_layout(
        yaxis=dict(tickformat=".0%", range=[0, 1.1]),
        xaxis=dict(tickangle=-45),
        height=500, paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)'
    )
    st.plotly_chart(fig_l, use_container_width=True)

    st.info("💡 Nota: Se han omitido los registros con 0% para evitar que la línea de avance caiga artificialmente si el mes aún no cierra.")
else:
    st.warning("Asegúrate de que tus hojas de Google Sheets estén publicadas como CSV y contengan datos válidos.")
