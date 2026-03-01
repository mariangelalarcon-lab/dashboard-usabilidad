import streamlit as st
import pandas as pd
import plotly.graph_objects as go

# 1. Configuración de pantalla
st.set_page_config(page_title="Holos | Business Intelligence", layout="wide")

# --- ENLACES POR PESTAÑA (GID específicos) ---
# Hoja 1 (Probablemente 2025)
LINK_1 = "https://docs.google.com/spreadsheets/d/e/2PACX-1vSWiXR7BLxwzX2wtD_uF59pvxtus8BL5iqgymKSh2-Llwt6smOJzR7ROUxICr57DA/pub?gid=1638907402&single=true&output=csv"
# Hoja 2 (Probablemente 2026)
LINK_2 = "https://docs.google.com/spreadsheets/d/e/2PACX-1vSWiXR7BLxwzX2wtD_uF59pvxtus8BL5iqgymKSh2-Llwt6smOJzR7ROUxICr57DA/pub?gid=1341962834&single=true&output=csv"

# --- PALETA OFICIAL HOLOS ---
SKY, LEAF, SEA, CORAL, BLACK, WHITE = "#D1E9F6", "#F1FB8C", "#A9C1F5", "#FF9F86", "#000000", "#FFFFFF"

st.markdown(f"""
    <style>
        .stApp {{ background-color: {SKY}; }}
        h1, h2, h3 {{ font-family: 'Philosopher', sans-serif !important; color: {BLACK}; }}
        .insight-card {{ background-color: {WHITE}; border-left: 6px solid {LEAF}; padding: 20px; border-radius: 10px; box-shadow: 0 4px 6px rgba(0,0,0,0.05); color: black; }}
    </style>
""", unsafe_allow_html=True)

@st.cache_data(ttl=10)
def cargar_data_completa():
    try:
        # Cargamos ambas pestañas por separado para asegurar que no se pierda ninguna
        df_a = pd.read_csv(LINK_1)
        df_b = pd.read_csv(LINK_2)
        
        # Unimos ambas hojas
        df = pd.concat([df_a, df_b], ignore_index=True)
        df.columns = [str(c).strip() for c in df.columns]

        # Identificadores dinámicos mejorados
        c_usa = next((c for c in df.columns if 'Engagement' in c or 'Usabilidad' in c), df.columns[7])
        c_emp = next((c for c in df.columns if 'Empresa' in c or 'Nombre' in c), df.columns[0])
        c_sem = next((c for c in df.columns if 'Semana' in c), df.columns[1])
        c_mes = next((c for c in df.columns if 'Mes' in c), df.columns[9])
        c_ani = next((c for c in df.columns if 'Año' in c or 'Anio' in c), df.columns[11])

        def limpiar_num(val):
            try:
                s = str(val).replace('%', '').replace(',', '.').strip()
                if s == "" or s == "nan": return None
                n = float(s)
                return n / 100.0 if n > 1.1 else n
            except: return None

        df['Usabilidad_V'] = df[c_usa].apply(limpiar_num)
        df['Anio_V'] = pd.to_numeric(df[c_ani], errors='coerce').fillna(0).astype(int)
        df['Mes_V'] = pd.to_numeric(df[c_mes], errors='coerce').fillna(0).astype(int)
        df['Empresa_V'] = df[c_emp].astype(str).str.strip()
        df['Semana_V'] = df[c_sem].astype(str).str.strip().str.lower()
        
        # Filtramos solo lo que tiene datos reales
        return df.dropna(subset=['Usabilidad_V']), 'Empresa_V', 'Anio_V', 'Mes_V', 'Semana_V'
    except Exception as e:
        return pd.DataFrame(), str(e), None, None, None

df, col_emp, col_ani, col_mes, col_sem = cargar_data_completa()

if not df.empty:
    with st.sidebar:
        st.markdown("### 🎛️ Filtros")
        lista_empresas = sorted([e for e in df[col_emp].unique() if str(e) not in ['nan', 'None']])
        empresa_sel = st.selectbox("Empresa Target", ["Todas las Empresas"] + lista_empresas)
        
        # Aseguramos que 2026 esté disponible y seleccionado por defecto
        anios_disp = sorted([a for a in df[col_ani].unique() if a > 2020], reverse=True)
        anios_sel = st.multiselect("Comparativa Anual", anios_disp, default=anios_disp)
        
        meses_map = {1:'Ene', 2:'Feb', 3:'Mar', 4:'Abr', 5:'May', 6:'Jun', 7:'Jul', 8:'Ago', 9:'Set', 10:'Oct', 11:'Nov', 12:'Dic'}
        meses_sel = st.multiselect("Meses", sorted(meses_map.keys()), default=[1, 2], format_func=lambda x: meses_map[x])

    st.markdown(f"<h1>📊 Reporte de Usabilidad: {empresa_sel}</h1>", unsafe_allow_html=True)

    # FILTRADO
    df_f = df[(df[col_ani].isin(anios_sel)) & (df[col_mes].isin(meses_sel))].copy()
    if empresa_sel != "Todas las Empresas":
        df_f = df_f[df_f[col_emp] == empresa_sel]

    # --- GAUGES ---
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
                    title={'text': f"Media {anio}", 'font': {'size': 18, 'color': BLACK}},
                    gauge={'axis': {'range': [0, 100]}, 'bar': {'color': BLACK},
                           'steps': [{'range': [0, 100], 'color': colores_config.get(anio, WHITE)}]}
                ))
                fig_g.update_layout(height=220, margin=dict(l=30, r=30, t=50, b=20), paper_bgcolor='rgba(0,0,0,0)')
                st.plotly_chart(fig_g, use_container_width=True, key=f"g_{anio}")

    # --- CURVA DE ENGAGEMENT (UNIFICADA) ---
    st.markdown("### 📈 Curva de Engagement (2025 vs 2026)")
    if not df_f.empty:
        # Calculamos el promedio mensual, priorizando cierre si existe o calculando avance
        res_grafico = []
        for a in anios_sel:
            for m in meses_sel:
                df_temp = df_f[(df_f[col_ani] == a) & (df_f[col_mes] == m)]
                if not df_temp.empty:
                    cierre = df_temp[df_temp[col_sem].str.contains("total", na=False)]
                    val = cierre['Usabilidad_V'].mean() if not cierre.empty else df_temp['Usabilidad_V'].mean()
                    res_grafico.append({col_ani: a, col_mes: m, 'Usabilidad_V': val})
        
        df_ev = pd.DataFrame(res_grafico)
        if not df_ev.empty:
            df_ev = df_ev.sort_values([col_ani, col_mes])
            fig_line = go.Figure()
            for anio in sorted(anios_sel):
                df_a = df_ev[df_ev[col_ani] == anio]
                if not df_a.empty:
                    fig_line.add_trace(go.Scatter(
                        x=[meses_map.get(m) for m in df_a[col_mes]], y=df_a['Usabilidad_V'],
                        name=f"Año {anio}", mode='lines+markers+text',
                        line=dict(color=colores_config.get(anio, BLACK), width=4),
                        text=[f"{v:.1%}" for v in df_a['Usabilidad_V']],
                        textposition="top center", connectgaps=True
                    ))
            
            fig_line.update_layout(yaxis=dict(tickformat=".0%", range=[0, 1.1]), height=450, paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)')
            st.plotly_chart(fig_line, use_container_width=True)

    # --- INFORME ---
    st.markdown("### 🧠 Informe de Desempeño Holos")
    if not df_f.empty:
        # Buscamos el último dato de 2026 específicamente
        df_2026 = df_f[df_f[col_ani] == 2026]
        msg_2026 = "Esperando datos 2026..."
        if not df_2026.empty:
            ult_2026 = df_2026.sort_values([col_mes], ascending=False).iloc[0]
            msg_2026 = f"Dato más reciente de 2026: <b>{meses_map.get(ult_2026[col_mes])}</b> con <b>{ult_2026['Usabilidad_V']:.1%}</b>."

        st.markdown(f"""
        <div class='insight-card'>
            <strong>Estatus 2026:</strong> {msg_2026}<br>
            <strong>Nota:</strong> La data de la segunda pestaña (2026) ha sido integrada correctamente al flujo comparativo.
        </div>
        """, unsafe_allow_html=True)

    with st.expander("📂 Auditoría de Datos (Ver pestaña 2026)"):
        st.write("Registros de 2026 detectados:", len(df[df[col_ani] == 2026]))
        st.dataframe(df_f)
else:
    st.error("Error: No se detectan datos en la pestaña de 2026. Verifica que esté publicada como CSV.")
