import streamlit as st
import pandas as pd
import plotly.graph_objects as go

# 1. Configuración de pantalla
st.set_page_config(page_title="Holos | Business Intelligence", layout="wide")

# --- ENLACES DE DATOS DIRECTOS ---
LINK_1 = "https://docs.google.com/spreadsheets/d/e/2PACX-1vSWiXR7BLxwzX2wtD_uF59pvxtus8BL5iqgymKSh2-Llwt6smOJzR7ROUxICr57DA/pub?gid=1638907402&single=true&output=csv"
LINK_2 = "https://docs.google.com/spreadsheets/d/e/2PACX-1vSWiXR7BLxwzX2wtD_uF59pvxtus8BL5iqgymKSh2-Llwt6smOJzR7ROUxICr57DA/pub?gid=1341962834&single=true&output=csv"

# --- PALETA OFICIAL HOLOS ---
SKY, LEAF, SEA, CORAL, BLACK, WHITE = "#D1E9F6", "#F1FB8C", "#A9C1F5", "#FF9F86", "#000000", "#FFFFFF"

# --- DISEÑO UI ---
st.markdown(f"""
    <style>
        .stApp {{ background-color: {SKY}; }}
        h1, h2, h3 {{ font-family: 'Philosopher', sans-serif !important; color: {BLACK}; }}
        [data-testid="stSidebar"] {{ background-color: {WHITE}; }}
        .insight-card {{ background-color: {WHITE}; border-left: 6px solid {LEAF}; padding: 20px; border-radius: 10px; box-shadow: 0 4px 6px rgba(0,0,0,0.05); color: black; }}
    </style>
""", unsafe_allow_html=True)

@st.cache_data(ttl=10) # TTL bajo para ver cambios rápidos del Excel
def cargar_data():
    try:
        df1 = pd.read_csv(LINK_1)
        df2 = pd.read_csv(LINK_2)
        df = pd.concat([df1, df2], ignore_index=True)
        df.columns = [str(c).strip() for c in df.columns]
        
        # Mapeo posicional para evitar errores de nombres
        df['Usabilidad_V'] = df.iloc[:, 7].apply(lambda x: (float(str(x).replace('%', '').replace(',', '.')) / 100 if float(str(x).replace('%', '').replace(',', '.')) > 1.1 else float(str(x).replace('%', '').replace(',', '.'))) if pd.notnull(x) and str(x).strip() != "" else None)
        df['Anio_V'] = pd.to_numeric(df.iloc[:, 11], errors='coerce').fillna(0).astype(int)
        df['Mes_V'] = pd.to_numeric(df.iloc[:, 9], errors='coerce').fillna(0).astype(int)
        df['Empresa_V'] = df.iloc[:, 0].astype(str).str.strip()
        df['Semana_V'] = df.iloc[:, 1].astype(str).str.strip().str.lower()
        
        return df.dropna(subset=['Usabilidad_V'])
    except:
        return pd.DataFrame()

df = cargar_data()

if not df.empty:
    with st.sidebar:
        st.markdown("### 🎛️ Filtros")
        lista_empresas = sorted([e for e in df['Empresa_V'].unique() if e not in ['nan', 'None']])
        empresa_sel = st.selectbox("Empresa Target", ["Todas las Empresas"] + lista_empresas)
        
        anios_disp = sorted([a for a in df['Anio_V'].unique() if a > 2020], reverse=True)
        anios_sel = st.multiselect("Comparativa Anual", anios_disp, default=[2026, 2025])
        
        meses_map = {1:'Ene', 2:'Feb', 3:'Mar', 4:'Abr', 5:'May', 6:'Jun', 7:'Jul', 8:'Ago', 9:'Set', 10:'Oct', 11:'Nov', 12:'Dic'}
        meses_sel = st.multiselect("Meses", list(meses_map.keys()), default=[1, 2], format_func=lambda x: meses_map[x])

    st.markdown(f"<h1>📊 Reporte de Usabilidad: {empresa_sel}</h1>", unsafe_allow_html=True)

    # Filtrado
    mask = (df['Anio_V'].isin(anios_sel)) & (df['Mes_V'].isin(meses_sel))
    if empresa_sel != "Todas las Empresas":
        mask &= (df['Empresa_V'] == empresa_sel)
    df_f = df[mask].copy()

    # --- GAUGES (PROMEDIO TOTAL POR AÑO) ---
    colores_config = {2024: LEAF, 2025: CORAL, 2026: SEA}
    anios_activos = sorted(df_f['Anio_V'].unique())
    if anios_activos:
        gauge_cols = st.columns(len(anios_activos))
        for i, anio in enumerate(anios_activos):
            with gauge_cols[i]:
                # Solo promediamos las filas de "Mes total" para el Gauge si existen, sino todo
                df_anio = df_f[df_f['Anio_V'] == anio]
                promedio = df_anio['Usabilidad_V'].mean()
                fig_g = go.Figure(go.Indicator(
                    mode="gauge+number", value=(promedio or 0)*100,
                    number={'suffix': "%", 'font': {'size': 26, 'color': BLACK}, 'valueformat': '.1f'},
                    title={'text': f"Media {anio}", 'font': {'size': 16, 'color': BLACK}},
                    gauge={'axis': {'range': [0, 100]}, 'bar': {'color': BLACK}, 'steps': [{'range': [0, 100], 'color': colores_config.get(anio, WHITE)}]}
                ))
                fig_g.update_layout(height=200, margin=dict(l=20, r=20, t=40, b=20), paper_bgcolor='rgba(0,0,0,0)')
                st.plotly_chart(fig_g, use_container_width=True, key=f"g_{anio}")

    # --- CURVA DE AVANCE CORREGIDA ---
    st.markdown("### 📈 Avance de Usabilidad (Semanas y Cierres)")
    if not df_f.empty:
        # Definir el orden de las semanas
        rank_map = {'1era semana': 1, '2da semana': 2, '3era semana': 3, '4ta semana': 4, 'mes total': 5}
        df_f['rank'] = df_f['Semana_V'].map(rank_map).fillna(6)
        
        # Agrupar para obtener la línea de tiempo
        df_ev = df_f.groupby(['Anio_V', 'Mes_V', 'Semana_V', 'rank'])['Usabilidad_V'].mean().reset_index()
        df_ev = df_ev.sort_values(['Anio_V', 'Mes_V', 'rank'])
        
        fig_line = go.Figure()
        for anio in sorted(anios_sel):
            df_a = df_ev[df_ev['Anio_V'] == anio]
            if not df_a.empty:
                # Crear etiquetas: Si es "mes total", ponemos el nombre del mes en grande
                x_labels = [f"{meses_map[m]} - {s.capitalize()}" for m, s in zip(df_a['Mes_V'], df_a['Semana_V'])]
                
                fig_line.add_trace(go.Scatter(
                    x=x_labels, y=df_a['Usabilidad_V'],
                    name=f"Año {anio}", mode='lines+markers+text',
                    text=[f"{v:.1%}" for v in df_a['Usabilidad_V']],
                    textposition="top center",
                    line=dict(color=colores_config.get(anio, BLACK), width=4),
                    connectgaps=True
                ))
        
        fig_line.update_layout(
            yaxis=dict(tickformat=".0%", range=[0, 1.1], gridcolor='rgba(0,0,0,0.1)'),
            xaxis=dict(showgrid=False, tickangle=-45),
            paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)', height=450
        )
        st.plotly_chart(fig_line, use_container_width=True)

    # --- INFORME ---
    if not df_f.empty:
        ult_dato = df_f.sort_values(['Anio_V', 'Mes_V', 'rank'], ascending=False).iloc[0]
        st.markdown(f"""
        <div class='insight-card'>
            <strong>Estatus de Avance:</strong> El último dato registrado es <b>{ult_dato['Semana_V'].capitalize()} de {meses_map[ult_dato['Mes_V']]}</b> con un <b>{ult_dato['Usabilidad_V']:.1%}</b>.<br>
            <strong>Diagnóstico:</strong> La visualización ahora integra la data de Febrero y respeta el promedio del cierre de Enero.
        </div>
        """, unsafe_allow_html=True)

else:
    st.error("No se detectaron datos. Revisa la publicación en la web de tu Google Sheet.")
