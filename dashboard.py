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
    <link href="https://fonts.googleapis.com/css2?family=Philosopher:wght@700&family=Inter:wght@400;600&display=swap" rel="stylesheet">
    <style>
        .stApp {{ background-color: {SKY}; }}
        h1, h2, h3 {{ font-family: 'Philosopher', sans-serif !important; color: {BLACK}; }}
        * {{ font-family: 'Inter', sans-serif; }}
        [data-testid="stSidebar"] {{ background-color: {WHITE}; }}
        .insight-card {{ background-color: {WHITE}; border-left: 6px solid {LEAF}; padding: 20px; border-radius: 10px; box-shadow: 0 4px 6px rgba(0,0,0,0.05); }}
    </style>
""", unsafe_allow_html=True)

@st.cache_data(ttl=60) # Bajé el TTL a 60 segundos para que veas tus cambios del Excel casi al instante
def cargar_data():
    try:
        df1 = pd.read_csv(LINK_1)
        df2 = pd.read_csv(LINK_2)
        df = pd.concat([df1, df2], ignore_index=True)
        df.columns = [str(c).strip() for c in df.columns]
        
        # Identificar columnas dinámicamente
        c_usa = next((c for c in df.columns if 'Engagement' in c or 'Usabilidad' in c), None)
        c_emp = next((c for c in df.columns if 'Empresa' in c or 'Nombre' in c), df.columns[0])
        c_sem = next((c for c in df.columns if 'Semana' in c), None) # NUEVA: Para el progreso semanal
        c_mes = next((c for c in df.columns if 'Mes' in c), None)
        c_ani = next((c for c in df.columns if 'Año' in c or 'Anio' in c), None)

        def limpiar_num(val):
            try:
                s = str(val).replace('%', '').replace(',', '.').strip()
                n = float(s)
                return n / 100.0 if n > 1.1 else n
            except: return 0.0

        df['Usabilidad_V'] = df[c_usa].apply(limpiar_num)
        df['Anio_V'] = pd.to_numeric(df[c_ani], errors='coerce').fillna(0).astype(int)
        df['Mes_V'] = pd.to_numeric(df[c_mes], errors='coerce').fillna(0).astype(int)
        df['Empresa_V'] = df[c_emp].astype(str).str.strip()
        df['Semana_V'] = df[c_sem].astype(str).str.strip() if c_sem else ""
        
        return df, 'Empresa_V', 'Anio_V', 'Mes_V', 'Semana_V'
    except Exception as e:
        return pd.DataFrame(), str(e), None, None, None

df, col_emp, col_ani, col_mes, col_sem = cargar_data()

if not df.empty:
    with st.sidebar:
        st.markdown("### 🎛️ Filtros")
        lista_empresas = sorted([e for e in df[col_emp].unique() if str(e) not in ['nan', 'None']])
        empresa_sel = st.selectbox("Empresa Target", ["Todas las Empresas"] + lista_empresas)
        
        anios_disp = sorted([a for a in df[col_ani].unique() if a > 2020], reverse=True)
        anios_sel = st.multiselect("Comparativa Anual", anios_disp, default=anios_disp)
        
        meses_map = {1:'Ene', 2:'Feb', 3:'Mar', 4:'Abr', 5:'May', 6:'Jun', 7:'Jul', 8:'Ago', 9:'Set', 10:'Oct', 11:'Nov', 12:'Dic'}
        meses_sel = st.multiselect("Meses", sorted(meses_map.keys()), 
                                   default=sorted(meses_map.keys()), format_func=lambda x: meses_map[x])

    st.markdown(f"<h1>📊 Reporte de Usabilidad: {empresa_sel}</h1>", unsafe_allow_html=True)

    # FILTRADO
    df_f = df[(df[col_ani].isin(anios_sel)) & (df[col_mes].isin(meses_sel))].copy()
    if empresa_sel != "Todas las Empresas":
        df_f = df_f[df_f[col_emp] == empresa_sel]

    # --- GAUGES (SE MANTIENEN IGUAL) ---
    colores_config = {2024: LEAF, 2025: CORAL, 2026: SEA}
    anios_activos = sorted(df_f[col_ani].unique())
    
    if anios_activos:
        gauge_cols = st.columns(len(anios_activos))
        for i, anio in enumerate(anios_activos):
            with gauge_cols[i]:
                promedio = df_f[df_f[col_ani] == anio]['Usabilidad_V'].mean()
                fig_g = go.Figure(go.Indicator(
                    mode="gauge+number", value=(promedio or 0)*100,
                    number={'suffix': "%", 'font': {'size': 28, 'color': BLACK}, 'valueformat': '.1f'},
                    title={'text': f"Promedio {anio}", 'font': {'size': 18, 'color': BLACK}},
                    gauge={'axis': {'range': [0, 100], 'tickcolor': BLACK},
                           'bar': {'color': BLACK},
                           'steps': [{'range': [0, 100], 'color': colores_config.get(anio, WHITE)}]}
                ))
                fig_g.update_layout(height=220, margin=dict(l=30, r=30, t=50, b=20), paper_bgcolor='rgba(0,0,0,0)')
                st.plotly_chart(fig_g, use_container_width=True, key=f"gauge_{anio}")

    # --- CURVA DE ENGAGEMENT CON PROGRESO SEMANAL ---
    st.markdown("### 📈 Curva de Progreso (Mensual/Semanal)")
    if not df_f.empty:
        # Lógica para ordenar semanas: '1era' < '2da' < '3era' < '4ta' < 'Mes total'
        rank_sem = {'1era semana': 1, '2da semana': 2, '3era semana': 3, '4ta semana': 4, 'mes total': 5}
        df_f['rank_s'] = df_f[col_sem].str.lower().map(rank_sem).fillna(6)
        
        # Agrupamos por año, mes y semana para ver el progreso real
        df_ev = df_f.groupby([col_ani, col_mes, col_sem, 'rank_s'])['Usabilidad_V'].mean().reset_index()
        df_ev = df_ev.sort_values([col_ani, col_mes, 'rank_s'])
        
        fig_line = go.Figure()
        for anio in sorted(anios_sel):
            df_a = df_ev[df_ev[col_ani] == anio]
            if not df_a.empty:
                # ETIQUETA: Si es "Mes total" solo ponemos el nombre del mes, si no, ponemos la semana
                labels_x = []
                for m, s in zip(df_a[col_mes], df_a[col_sem]):
                    if 'total' in s.lower(): labels_x.append(f"{meses_map.get(m)}")
                    else: labels_x.append(f"{meses_map.get(m)} - {s}")

                fig_line.add_trace(go.Scatter(
                    x=labels_x, 
                    y=df_a['Usabilidad_V'],
                    name=f"Año {anio}", 
                    mode='lines+markers+text',
                    line=dict(color=colores_config.get(anio, BLACK), width=4),
                    text=[f"{v:.1%}" for v in df_a['Usabilidad_V']],
                    textposition="top center",
                    connectgaps=True
                ))
        
        fig_line.update_layout(
            yaxis=dict(tickformat=".0%", range=[0, 1.1], gridcolor='rgba(0,0,0,0.1)'),
            xaxis=dict(showgrid=False, tickangle=-45),
            paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)',
            height=500, legend=dict(orientation="h", y=1.1, x=0.5, xanchor="center")
        )
        st.plotly_chart(fig_line, use_container_width=True)

    # --- INFORME INTELIGENTE ---
    st.markdown("### 🧠 Informe de Desempeño Holos")
    if not df_f.empty:
        # Usabilidad del último dato registrado (Semana 1 Feb en este caso)
        ult_df = df_f.sort_values([col_ani, col_mes, 'rank_s'], ascending=False).iloc[0]
        total_avg = df_f['Usabilidad_V'].mean()
        
        st.markdown(f"""
        <div class='insight-card'>
            <strong>Análisis Ejecutivo:</strong> El nivel de usabilidad promedio general es de <b>{total_avg:.1%}</b>.<br>
            <strong>Estado Actual:</strong> Se ha integrado la data de <b>{ult_df[col_sem]}</b> de <b>{meses_map.get(ult_df[col_mes])}</b> con un rendimiento de <b>{ult_df['Usabilidad_V']:.1%}</b>.<br>
            <strong>Insight:</strong> La curva refleja el progreso en tiempo real de {max(anios_sel)}. Se recomienda comparar el cierre de Enero con este primer avance de Febrero para validar la retención.
        </div>
        """, unsafe_allow_html=True)

    with st.expander("📂 Explorar registros detallados"):
        st.dataframe(df_f[[col_emp, col_ani, col_mes, col_sem, 'Usabilidad_V']])
else:
    st.error("No se detectaron datos. Revisa la conexión con Google Sheets.")
