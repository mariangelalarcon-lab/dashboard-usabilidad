import streamlit as st
import pandas as pd
import plotly.graph_objects as go
from streamlit_gsheets import GSheetsConnection

# 1. Configuración de página
st.set_page_config(page_title="Reporte de Usabilidad | Holos", layout="wide")

# --- ESTILO CSS PREMIUM ---
st.markdown("""
    <link href="https://fonts.googleapis.com/css2?family=Philosopher:wght@700&family=Inter:wght@400;600&display=swap" rel="stylesheet">
    <style>
        .stApp { background-color: #D1E9F6; }
        h1, h2, h3 { font-family: 'Philosopher', sans-serif !important; color: #1E293B; }
        * { font-family: 'Inter', sans-serif; }
        .stMetric { background-color: white; padding: 15px; border-radius: 10px; box-shadow: 0 2px 4px rgba(0,0,0,0.05); }
        [data-testid="stSidebar"] { background-color: #FFFFFF; }
    </style>
""", unsafe_allow_html=True)

@st.cache_data(ttl=300)
def load_and_clean_data():
    conn = st.connection("gsheets", type=GSheetsConnection)
    try:
        # Intentar cargar ambas pestañas
        df1 = conn.read(worksheet="2024-2025")
        df2 = conn.read(worksheet="2026")
        df = pd.concat([df1, df2], ignore_index=True)
    except:
        df = conn.read() # Fallback

    df.columns = [str(c).strip() for c in df.columns]
    
    # Identificación de columnas
    c_usa = next((c for c in df.columns if 'Engagement' in c or 'Usabilidad' in c), None)
    c_emp = next((c for c in df.columns if 'Empresa' in c or 'Nombre' in c), df.columns[0])
    c_mes = next((c for c in df.columns if 'Mes' in c), None)
    c_ani = next((c for c in df.columns if 'Año' in c or 'Anio' in c), None)

    # Limpieza de valores numéricos
    def to_float(val):
        try:
            s = str(val).replace('%', '').replace(',', '.').strip()
            n = float(s)
            return n / 100.0 if n > 1.1 else n
        except: return 0.0

    df['Val_Usa'] = df[c_usa].apply(to_float)
    df['Anio_L'] = pd.to_numeric(df[c_ani], errors='coerce').fillna(0).astype(int)
    df['Mes_L'] = pd.to_numeric(df[c_mes], errors='coerce').fillna(0).astype(int)
    df['Empresa_L'] = df[c_emp].astype(str).str.strip()
    
    return df, 'Empresa_L', 'Anio_L', 'Mes_L'

try:
    df, col_emp, col_ani, col_mes = load_and_clean_data()

    # --- SIDEBAR ---
    with st.sidebar:
        st.header("🎛️ Filtros")
        empresas = sorted([e for e in df[col_emp].unique() if str(e) != 'nan'])
        emp_sel = st.selectbox("Selecciona Empresa", ["Todas las Empresas"] + empresas)
        
        anios_disp = sorted([a for a in df[col_ani].unique() if a > 2000], reverse=True)
        anios_sel = st.multiselect("Años a mostrar", anios_disp, default=anios_disp)
        
        meses_map = {1:'Ene', 2:'Feb', 3:'Mar', 4:'Abr', 5:'May', 6:'Jun', 7:'Jul', 8:'Ago', 9:'Set', 10:'Oct', 11:'Nov', 12:'Dic'}
        meses_sel = st.multiselect("Filtrar Meses", sorted(meses_map.keys()), 
                                   default=sorted(meses_map.keys()), format_func=lambda x: meses_map[x])

    st.title(f"📊 Reporte de Usabilidad: {emp_sel}")

    # Filtrado final
    df_f = df[(df[col_ani].isin(anios_sel)) & (df[col_mes].isin(meses_sel))].copy()
    if emp_sel != "Todas las Empresas":
        df_f = df_f[df_f[col_emp] == emp_sel]

    # --- GAUGES ---
    colores = {2024: "#F1FB8C", 2025: "#FF9F86", 2026: "#A9C1F5"}
    
    anios_activos = sorted(df_f[col_ani].unique())
    if anios_activos:
        cols = st.columns(len(anios_activos))
        for i, a in enumerate(anios_activos):
            with cols[i]:
                val = df_f[df_f[col_ani] == a]['Val_Usa'].mean()
                fig_g = go.Figure(go.Indicator(
                    mode="gauge+number", value=val*100,
                    number={'suffix': "%", 'font': {'size': 26}},
                    title={'text': f"Promedio {a}", 'font': {'size': 18}},
                    gauge={'axis': {'range': [0, 100]}, 'bar': {'color': '#1E293B'},
                           'steps': [{'range': [0, 100], 'color': colores.get(a, "#EEE")}]}
                ))
                fig_g.update_layout(height=180, margin=dict(l=20, r=20, t=40, b=10), paper_bgcolor='rgba(0,0,0,0)')
                st.plotly_chart(fig_g, use_container_width=True, key=f"g_{a}")

    # --- GRÁFICA DE EVOLUCIÓN (CURVA DE ENGAGEMENT) ---
    st.markdown("### 📈 Curva de Engagement")
    if not df_f.empty:
        df_ev = df_f.groupby([col_mes, col_ani])['Val_Usa'].mean().reset_index()
        fig_line = go.Figure()
        
        for a in sorted(anios_sel):
            df_a = df_ev[df_ev[col_ani] == a].sort_values(col_mes)
            if not df_a.empty:
                # Evitamos el error de meses mapeando solo si el mes existe en meses_map
                nombres_meses = [meses_map.get(m, str(m)) for m in df_a[col_mes]]
                fig_line.add_trace(go.Scatter(
                    x=nombres_meses, y=df_a['Val_Usa'],
                    name=f"Año {a}", mode='lines+markers+text',
                    line=dict(color=colores.get(a), width=4),
                    text=[f"{v:.1%}" for v in df_a['Val_Usa']],
                    textposition="top center"
                ))
        
        fig_line.update_layout(
            yaxis=dict(tickformat=".0%", range=[0, 1.1], gridcolor='rgba(0,0,0,0.1)'),
            paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)',
            height=400, legend=dict(orientation="h", y=1.1, x=0.5, xanchor="center")
        )
        st.plotly_chart(fig_line, use_container_width=True)

    # --- INFORME INTELIGENTE ---
    st.markdown("### 🧠 Informe de Desempeño")
    c1, c2 = st.columns(2)
    if not df_f.empty:
        avg_actual = df_f['Val_Usa'].mean()
        mejor_mes = df_f.groupby(col_mes)['Val_Usa'].mean().idxmax()
        with c1:
            st.info(f"💡 **Promedio General:** La usabilidad consolidada bajo estos filtros es de **{avg_actual:.1%}**.")
        with c2:
            st.success(f"🌟 **Hito Histórico:** El mes con mayor engagement ha sido **{meses_map.get(mejor_mes)}**.")

    with st.expander("📂 Ver registros detallados"):
        st.dataframe(df_f)

except Exception as e:
    st.error(f"Se detectó un error en los datos: {e}")
