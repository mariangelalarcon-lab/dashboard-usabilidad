import streamlit as st
import pandas as pd
import plotly.graph_objects as go

# 1. Configuración de página
st.set_page_config(page_title="Reporte de Usabilidad - Beholos", layout="wide")

# --- ENLACES REALES ---
LINK_1 = "https://docs.google.com/spreadsheets/d/e/2PACX-1vSWiXR7BLxwzX2wtD_uF59pvxtus8BL5iqgymKSh2-Llwt6smOJzR7ROUxICr57DA/pub?gid=1638907402&single=true&output=csv"
LINK_2 = "https://docs.google.com/spreadsheets/d/e/2PACX-1vSWiXR7BLxwzX2wtD_uF59pvxtus8BL5iqgymKSh2-Llwt6smOJzR7ROUxICr57DA/pub?gid=1341962834&single=true&output=csv"

# --- ESTILO CSS ---
st.markdown("""
    <style>
        .stApp { background-color: #D1E9F6; } 
        h1 { color: #1E293B; font-family: 'Arial'; font-weight: bold; }
        .stExpander { background-color: white !important; border-radius: 10px; }
    </style>
""", unsafe_allow_html=True)

@st.cache_data(ttl=300)
def cargar_datos_completos():
    try:
        df1 = pd.read_csv(LINK_1)
        df2 = pd.read_csv(LINK_2)
        df = pd.concat([df1, df2], ignore_index=True)
        df.columns = [str(c).strip() for c in df.columns]
        
        # Buscador de columnas clave
        c_emp = next((c for c in df.columns if 'Empresa' in c or 'Nombre' in c), df.columns[0])
        c_usa = next((c for c in df.columns if 'Engagement' in c or 'Usabilidad' in c), None)
        c_ani = next((c for c in df.columns if 'Año' in c or 'Anio' in c), None)
        c_mes = next((c for c in df.columns if 'Mes' in c), None)

        # Limpieza de valores
        df['Val_Usa'] = pd.to_numeric(df[c_usa].astype(str).str.replace('%', '').str.replace(',', '.'), errors='coerce').fillna(0)
        if df['Val_Usa'].max() > 1.1: df['Val_Usa'] = df['Val_Usa'] / 100
        
        df['Anio_Limpio'] = pd.to_numeric(df[c_ani], errors='coerce').fillna(0).astype(int)
        df['Mes_Limpio'] = pd.to_numeric(df[c_mes], errors='coerce').fillna(0).astype(int)
        
        return df, c_emp, 'Anio_Limpio', 'Mes_Limpio'
    except Exception as e:
        st.error(f"Error: {e}")
        return pd.DataFrame(), None, None, None

df, col_emp, col_ani, col_mes = cargar_datos_completos()

if not df.empty:
    with st.sidebar:
        st.header("🎛️ Filtros")
        empresas = sorted([e for e in df[col_emp].unique() if str(e) != 'nan'])
        emp_sel = st.selectbox("Selecciona Empresa", ["Todas las Empresas"] + empresas)
        
        anios_disp = sorted([a for a in df[col_ani].unique() if a > 2000], reverse=True)
        anios_sel = st.multiselect("Años a mostrar", anios_disp, default=anios_disp)

    st.title(f"📊 Reporte de Usabilidad: {emp_sel}")

    # Filtrado
    df_f = df[df[col_ani].isin(anios_sel)].copy()
    if emp_sel != "Todas las Empresas":
        df_f = df_f[df_f[col_emp] == emp_sel]

    # --- 1. INDICADORES (GAUGES) ---
    colores = {2024: "#F1FB8C", 2025: "#FF9F86", 2026: "#A9C1F5", 2023: "#CBD5E1"}
    
    anios_finales = sorted(df_f[col_ani].unique())
    if anios_finales:
        cols = st.columns(len(anios_finales))
        for i, a in enumerate(anios_finales):
            with cols[i]:
                val = df_f[df_f[col_ani] == a]['Val_Usa'].mean()
                fig = go.Figure(go.Indicator(
                    mode="gauge+number", value=val*100,
                    number={'suffix': "%", 'font': {'size': 24}},
                    title={'text': f"Promedio {a}", 'font': {'size': 18}},
                    gauge={'axis': {'range': [0, 100]}, 'bar': {'color': "#1E293B"},
                           'steps': [{'range': [0, 100], 'color': colores.get(a, "#EEE")}]}
                ))
                fig.update_layout(height=200, margin=dict(l=20, r=20, t=40, b=10), paper_bgcolor='rgba(0,0,0,0)')
                st.plotly_chart(fig, use_container_width=True, key=f"g_{a}")

    # --- 2. GRÁFICA DE EVOLUCIÓN ---
    st.markdown("### 📈 Evolución Estratégica")
    meses_map = {1:'Ene', 2:'Feb', 3:'Mar', 4:'Abr', 5:'May', 6:'Jun', 7:'Jul', 8:'Ago', 9:'Set', 10:'Oct', 11:'Nov', 12:'Dic'}
    
    df_ev = df_f.groupby([col_mes, col_ani])['Val_Usa'].mean().reset_index()
    fig_line = go.Figure()
    
    for a in sorted(anios_sel):
        df_a = df_ev[df_ev[col_ani] == a].sort_values(col_mes)
        if not df_a.empty:
            fig_line.add_trace(go.Scatter(
                x=[meses_map.get(m, m) for m in df_a[col_mes]], 
                y=df_a['Val_Usa'],
                name=f"Año {a}", mode='lines+markers+text',
                text=[f"{v:.1%}" for v in df_a['Val_Usa']],
                textposition="top center",
                line=dict(color=colores.get(a), width=4)
            ))

    fig_line.update_layout(
        yaxis=dict(tickformat=".0%", range=[0, 1.1]),
        paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)',
        height=400, legend=dict(orientation="h", y=1.1)
    )
    st.plotly_chart(fig_line, use_container_width=True)

    # --- 3. TABLA ---
    with st.expander("📂 Ver registros detallados"):
        st.dataframe(df_f)
