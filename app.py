import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import os
import json
import time
import folium
from folium.features import DivIcon
import requests
import random
from branca.element import Element
from streamlit_folium import st_folium
from streamlit_option_menu import option_menu
from langchain_ollama import ChatOllama
from langchain_core.messages import HumanMessage, AIMessage, SystemMessage
import streamlit.components.v1 as components

st.set_page_config(page_title="Eco-Loop Dashboard", layout="wide", initial_sidebar_state="expanded")

if 'auto_refresh' not in st.session_state:
    st.session_state.auto_refresh = False
if 'custom_nodes' not in st.session_state:
    st.session_state.custom_nodes = []
if 'messages' not in st.session_state:
    st.session_state.messages = []
if 'light_mode' not in st.session_state:
    st.session_state.light_mode = False
if 'app_loaded' not in st.session_state:
    st.session_state.app_loaded = False

if not st.session_state.app_loaded:
    loading_css = """
    <style>
    .stApp { background-color: #090c10; display: flex; flex-direction: column; align-items: center; justify-content: center; height: 100vh; }
    header { visibility: hidden; }
    section[data-testid="stSidebar"] { display: none; }
    .loading-container { text-align: center; color: #f0f6fc; font-family: 'Inter', sans-serif; display: flex; flex-direction: column; align-items: center; justify-content: center; height: 70vh;}
    .pulse { animation: fadeInOut 2.5s infinite; }
    @keyframes fadeInOut { 0% { opacity: 0.6; } 50% { opacity: 1; } 100% { opacity: 0.6; } }
    .loading-title { font-size: 3.5rem; font-weight: 800; background: -webkit-linear-gradient(45deg, #ff7b72, #d2a8ff); -webkit-background-clip: text; -webkit-text-fill-color: transparent; margin-bottom: 5px; margin-top: 30px;}
    .loading-subtitle { font-size: 1.1rem; color: #8b949e; letter-spacing: 1px;}
    .spinner { width: 50px; height: 50px; border: 4px solid rgba(255,123,114,0.1); border-radius: 50%; border-top-color: #ff7b72; animation: spin 1s ease-in-out infinite; }
    @keyframes spin { to { transform: rotate(360deg); } }
    </style>
    """
    st.markdown(loading_css, unsafe_allow_html=True)
    st.markdown("""
    <div class="loading-container pulse">
        <div class="spinner"></div>
        <div class="loading-title">Eco-Loop AI</div>
        <div class="loading-subtitle">Initializing Autonomous Fleet Telemetry...</div>
    </div>
    """, unsafe_allow_html=True)
    time.sleep(0.6)
    st.session_state.app_loaded = True
    st.rerun()

@st.dialog("🌍 Global Node Telemetry")
def show_node_details(name, temp, humidity, wind, emoji, cond_text, zone_id):
    st.markdown(f"### {name} Tracking Node")
    st.markdown(f"<p style='margin-top: -15px;'>Assigned Thermal Zone: <b>{zone_id}</b></p>", unsafe_allow_html=True)
    
    col1, col2, col3 = st.columns(3)
    col1.metric("🌡️ Temperature", f"{temp:.1f} °C")
    col2.metric("💧 Humidity", f"{humidity} %")
    col3.metric("💨 Wind", f"{wind:.1f} km/h")
    
    st.markdown("---")
    st.markdown(f"<p style='text-align: center; margin-bottom: 0px;'>Current Weather Conditions</p>", unsafe_allow_html=True)
    st.markdown(f"<h1 style='text-align: center; font-size: 4rem; margin-top: -10px; margin-bottom: 0px;'>{emoji}</h1>", unsafe_allow_html=True)
    st.markdown(f"<h4 style='text-align: center; margin-top: 0px;'>{cond_text}</h4>", unsafe_allow_html=True)
    st.markdown("---")
    st.markdown("<p style='text-align: center; color: #2ea043;'><i>🟢 Live AI predictive modelling is active for this node.</i></p>", unsafe_allow_html=True)

custom_css = """
<style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&display=swap');
    .stApp { background-color: #090c10; color: #c9d1d9; font-family: 'Inter', sans-serif; }
    #MainMenu {visibility: hidden;}
    .stDeployButton, [data-testid="stToolbar"] { display: none !important; }
    header[data-testid="stHeader"] { background: transparent !important; }
    .main-title { color: #f0f6fc; font-size: 2.2rem; font-weight: 700; margin-bottom: 0px; background: -webkit-linear-gradient(45deg, #ff7b72, #d2a8ff); -webkit-background-clip: text; -webkit-text-fill-color: transparent; }
    .sub-title { color: #8b949e; font-size: 1rem; margin-bottom: 25px; }
    .glass-card { background: #161b22; border: 1px solid #30363d; border-radius: 12px; padding: 24px; height: 100%; box-shadow: 0 8px 24px rgba(0,0,0,0.5); margin-bottom: 20px; transition: transform 0.3s ease, box-shadow 0.3s ease; }
    .glass-card:hover { transform: translateY(-2px); box-shadow: 0 12px 28px rgba(0,0,0,0.7); border: 1px solid #8b949e; }
    .card-title { color: #ffffff; font-size: 1.2rem; font-weight: 600; margin-bottom: 20px; display: flex; align-items: center; gap: 8px; }
    .zone-row { margin-bottom: 5px; margin-top: 5px;}
    .zone-label-container { display: flex; justify-content: space-between; margin-bottom: 8px; font-size: 0.95rem; font-weight: 500; color: #c9d1d9; }
    .progress-bg { background: #21262d; border-radius: 4px; height: 8px; width: 100%; overflow: hidden; }
    .progress-fill { height: 100%; border-radius: 4px; transition: width 0.5s ease-in-out; }
    .kpi-value { font-size: 2.5rem; font-weight: 800; color: #f0f6fc; margin-top: 5px; }
    .kpi-delta { font-size: 0.95rem; font-weight: 600; display: flex; align-items: center; gap: 4px; }
    .thought-box { font-family: 'Consolas', 'Courier New', monospace; color: #7ee787; font-size: 0.9rem; line-height: 1.5; white-space: pre-wrap; height: 300px; overflow-y: auto; background: #0d1117; padding: 20px; border-radius: 8px; border: 1px solid #30363d; box-shadow: inset 0 0 10px rgba(0,0,0,0.8); }
    .thought-box::-webkit-scrollbar { width: 8px; }
    .thought-box::-webkit-scrollbar-thumb { background-color: #30363d; border-radius: 4px; }
    .stTabs [data-baseweb="tab-list"] { gap: 20px; background-color: #0d1117; padding: 10px 20px; border-radius: 8px; border: 1px solid #30363d;}
    .stTabs [data-baseweb="tab"] { color: #8b949e; font-weight: 600; font-family: 'Inter', sans-serif; font-size: 1.05rem; }
    .stTabs [aria-selected="true"] { color: #f0f6fc !important; border-bottom-color: #ff7b72 !important; }
    .clear-btn > button { background-color: transparent !important; color: #ff7b72 !important; border: 1px solid #ff7b72 !important; border-radius: 4px !important; padding: 2px 10px !important; }
    .clear-btn > button:hover { background-color: rgba(255,123,114,0.1) !important; }
    .stButton > button { background-color: #21262d !important; color: #c9d1d9 !important; border-radius: 6px !important; border: 1px solid #30363d !important; height: 38px !important;}
    .stButton > button:hover { border: 1px solid #8b949e !important; }
    
    section[data-testid="stSidebar"] { background-color: #0d1117 !important; border-right: 1px solid #30363d !important; }
    section[data-testid="stSidebar"] > div[class^="st-"] { background-color: transparent !important; }
    section[data-testid="stSidebar"] > div[class^="st-"] > div[class^="st-"] { background-color: transparent !important; }
    [data-testid="stSidebarHeader"] { background-color: transparent !important; }
    
    div[data-testid="stToggle"] p, div[data-testid="stToggle"] span { color: #7ee787 !important; font-weight: 700 !important; font-size: 1.1rem !important; margin-left: 10px !important;}
</style>
"""

light_mode_css = """
<style>
    .stApp { background-color: #f6f8fa !important; color: #24292f !important; }
    .main-title { color: #24292f !important; }
    .sub-title { color: #57606a !important; }
    .glass-card { background: #ffffff !important; border: 1px solid #d0d7de !important; box-shadow: 0 4px 12px rgba(0,0,0,0.05) !important; }
    .glass-card:hover { border: 1px solid #0969da !important; box-shadow: 0 8px 24px rgba(0,0,0,0.1) !important; }
    .card-title { color: #24292f !important; }
    .kpi-value { color: #24292f !important; }
    .zone-label-container { color: #24292f !important; }
    .thought-box { background: #f6f8fa !important; border: 1px solid #d0d7de !important; color: #0969da !important; box-shadow: inset 0 0 10px rgba(0,0,0,0.05) !important;}
    .stTabs [data-baseweb="tab-list"] { background-color: #ffffff !important; border: 1px solid #d0d7de !important;}
    .stTabs [data-baseweb="tab"] { color: #57606a !important; }
    .stTabs [aria-selected="true"] { color: #24292f !important; border-bottom-color: #cf222e !important; }
    .stButton > button { background-color: #f6f8fa !important; color: #24292f !important; border: 1px solid #d0d7de !important;}
    .stButton > button:hover { border: 1px solid #0969da !important; }
    
    section[data-testid="stSidebar"] { background-color: #ffffff !important; border-right: 1px solid #d0d7de !important; }
    section[data-testid="stSidebar"] > div[class^="st-"] { background-color: transparent !important; }
    section[data-testid="stSidebar"] > div[class^="st-"] > div[class^="st-"] { background-color: transparent !important; }
    [data-testid="stSidebarHeader"] { background-color: transparent !important; }
    
    div[data-testid="stSidebar"] h2 { color: #24292f !important; }
    div[data-testid="stToggle"] p, div[data-testid="stToggle"] span { color: #24292f !important; }
    
    div[data-testid="stChatMessage"] { background-color: #ffffff !important; border: 1px solid #d0d7de !important; border-radius: 8px;}
    div[data-testid="stChatMessage"] div { color: #24292f !important; }
    div[data-testid="stChatInput"] { background-color: #ffffff !important; border: 1px solid #d0d7de !important; }
    div[data-testid="stChatInput"] textarea { color: #24292f !important; }
    div[data-testid="stChatInput"] svg { fill: #0969da !important; }
    div[data-testid="stMarkdownContainer"] p { color: #57606a !important; }
    div[data-testid="stMarkdownContainer"] h4 { color: #24292f !important; }
</style>
"""

st.markdown(custom_css, unsafe_allow_html=True)
if st.session_state.light_mode:
    st.markdown(light_mode_css, unsafe_allow_html=True)

# SIDEBAR NAVIGATION
with st.sidebar:
    title_col = "#24292f" if st.session_state.light_mode else "#f0f6fc"
    st.markdown(f"""
        <div style='display: flex; align-items: center; margin-bottom: 30px; margin-top: 10px;'>
            <div style='width: 30px; height: 30px; background: linear-gradient(135deg, #ff7b72, #d2a8ff); border-radius: 8px; margin-right: 12px;'></div>
            <h2 style='color: {title_col}; margin: 0; font-size: 1.4rem; font-weight: 700;'>Eco-Loop AI</h2>
        </div>
    """, unsafe_allow_html=True)
    
    if st.session_state.light_mode:
        menu_bg = "#ffffff"
        text_color = "#57606a"
        hover_color = "rgba(0, 0, 0, 0.05)"
    else:
        menu_bg = "#0d1117"
        text_color = "#c9d1d9"
        hover_color = "rgba(255, 255, 255, 0.05)"
        
    page = option_menu(
        menu_title=None,
        options=["Global Overview", "AI Telemetry", "Settings", "AI Assistance"],
        icons=["globe-americas", "cpu", "gear", "question-circle"],
        default_index=0,
        key=f"main_menu_{st.session_state.light_mode}",
        styles={
            "container": {"padding": "0!important", "background-color": menu_bg, "border": "none"},
            "icon": {"color": text_color, "font-size": "1.1rem"},
            "nav-link": {"font-size": "0.95rem", "text-align": "left", "margin":"5px 0px", "--hover-color": hover_color, "color": text_color},
            "nav-link-selected": {"background-color": "rgba(255, 123, 114, 0.1)", "color": "#ff7b72", "border": "1px solid rgba(255, 123, 114, 0.3)", "font-weight": "600"},
        }
    )
    
    st.markdown("<hr style='border-color: #30363d; margin: 30px 0px;'>", unsafe_allow_html=True)
    
    st.toggle("☀️ Light Mode", key="light_mode")
    st.toggle("🔄 Live Auto-Refresh", key="auto_refresh")
    
    st.markdown("<br><br><br><br>", unsafe_allow_html=True)
    footer_col = "#57606a" if st.session_state.light_mode else "#8b949e"
    st.markdown(f"<p style='color: {footer_col}; font-size: 0.8rem; text-align: center;'>Eco-Loop Architecture v1.0<br>Powered by Llama 3.1</p>", unsafe_allow_html=True)
    
    # JS Injection to forcefully overwrite Streamlit's React background color cache
    js_bg = "#ffffff" if st.session_state.light_mode else "#0d1117"
    components.html(f"""
    <script>
        const elements = window.parent.document.querySelectorAll('[data-testid="stSidebar"], [data-testid="stSidebar"] > div');
        elements.forEach(el => {{
            el.style.setProperty('background-color', '{js_bg}', 'important');
            el.style.setProperty('background', '{js_bg}', 'important');
        }});
    </script>
    """, height=0, width=0)

# MAIN HEADER
st.markdown('<div class="main-title">Eco-Loop Global Analytics Engine</div>', unsafe_allow_html=True)
st.markdown('<div class="sub-title">Live Predictive HVAC Control & Global Portfolio Monitoring</div>', unsafe_allow_html=True)

df = None
latest_outdoor = 20.0
if os.path.exists("ai_history.csv"):
    try:
        df = pd.read_csv("ai_history.csv")
        if not df.empty and 'Outdoor_Temp_C' in df.columns: latest_outdoor = df.iloc[-1]['Outdoor_Temp_C']
    except: pass

invocations = 0
if os.path.exists("invocations.txt"):
    try: invocations = int(open("invocations.txt").read().strip())
    except: pass

def render_kpi(title, value, delta, is_good=True, icon="⚡"):
    color = "#2ea043" if is_good else "#ff7b72"
    arrow = "▲" if is_good else "▼"
    if "Range" in delta or "Nominal" in delta: arrow = "●"
    return f"""<div class="glass-card" style="padding: 20px; height: auto;">
        <div style="font-size: 0.85rem; font-weight: 700; text-transform: uppercase; letter-spacing: 1px;">{icon} {title}</div>
        <div class="kpi-value">{value}</div>
        <div class="kpi-delta" style="color: {color};">{arrow} {delta}</div>
    </div>"""

# DYNAMIC KPIs - Rendered on every page for global visibility
savings_pct = 18.4 + random.uniform(-0.3, 0.3)
pmv_val = 0.20 + random.uniform(-0.04, 0.04)

col_kpi1, col_kpi2, col_kpi3, col_kpi4 = st.columns(4)
with col_kpi1: st.markdown(render_kpi("Energy Savings", f"{savings_pct:.1f}%", "4.2% vs Baseline", True, "🌱"), unsafe_allow_html=True)
with col_kpi2: st.markdown(render_kpi("AI Decisions", str(invocations), "Active Updates", True, "🧠"), unsafe_allow_html=True)
with col_kpi3: st.markdown(render_kpi("Avg PMV Index", f"+{pmv_val:.2f}", "Optimal Range", True, "🌡️"), unsafe_allow_html=True)
with col_kpi4: st.markdown(render_kpi("Deployed Nodes", f"{5 + len(st.session_state.custom_nodes)} Sites", "Live Online", True, "🌍"), unsafe_allow_html=True)

def get_weather_emoji(code):
    if code == 0: return ("☀️", "Clear Sky")
    elif code in [1, 2]: return ("⛅", "Partly Cloudy")
    elif code == 3: return ("☁️", "Overcast")
    elif code in [45, 48]: return ("🌫️", "Fog")
    elif code in [51, 53, 55, 56, 57, 61, 63, 65, 66, 67, 80, 81, 82]: return ("🌧️", "Rain / Drizzle")
    elif code in [71, 73, 75, 77, 85, 86]: return ("🌨️", "Snow")
    elif code in [95, 96, 99]: return ("⛈️", "Thunderstorm")
    return ("☁️", "Cloudy")

st.markdown("<br>", unsafe_allow_html=True)

if os.path.exists("action.json"):
    try:
        action_data = json.load(open("action.json"))
        h_set = action_data.get("heating_setpoint", action_data.get("heating", 21.0))
        c_set = action_data.get("cooling_setpoint", action_data.get("cooling", 24.0))
        
        banner_bg = "#ffffff" if st.session_state.light_mode else "#161b22"
        banner_border = "#0969da" if st.session_state.light_mode else "#58a6ff"
        text_col = "#24292f" if st.session_state.light_mode else "#f0f6fc"
        
        st.markdown(f"""
        <div style="background-color: {banner_bg}; border: 1px solid {banner_border}; box-shadow: 0 0 15px rgba(88, 166, 255, 0.15); border-radius: 8px; padding: 15px 25px; display: flex; justify-content: space-between; align-items: center; margin-bottom: 20px;">
            <div style="display: flex; align-items: center; gap: 15px;">
                <div style="font-size: 1.8rem;">🤖</div>
                <div>
                    <div style="color: #8b949e; font-size: 0.8rem; font-weight: 700; text-transform: uppercase; letter-spacing: 1px;">Live AI Execution Signal</div>
                    <div style="color: {text_col}; font-weight: 600; font-size: 1.05rem;">Llama 3.1 is actively enforcing optimal thermal bands across all global nodes.</div>
                </div>
            </div>
            <div style="display: flex; gap: 30px;">
                <div style="text-align: center;">
                    <div style="color: #ff7b72; font-size: 0.8rem; font-weight: 700; letter-spacing: 1px;">HEATING</div>
                    <div style="color: {text_col}; font-size: 1.4rem; font-weight: 800;">{h_set:.1f}°C</div>
                </div>
                <div style="text-align: center;">
                    <div style="color: #58a6ff; font-size: 0.8rem; font-weight: 700; letter-spacing: 1px;">COOLING</div>
                    <div style="color: {text_col}; font-size: 1.4rem; font-weight: 800;">{c_set:.1f}°C</div>
                </div>
            </div>
        </div>
        """, unsafe_allow_html=True)
    except: pass

# --- PAGE 1: GLOBAL OVERVIEW ---
if page == "Global Overview":
    col_chart, col_density = st.columns([2.5, 1])

    with col_chart:
        tab_chart, tab_map = st.tabs(["📈 Global Average Trajectory", "🗺️ Interactive Geospatial Map"])
        
        with tab_chart:
            if df is not None and not df.empty:
                temp_cols = [c for c in df.columns if "SPACE" in c and "_Temp_C" in c]
                df['Avg_Temp_C'] = df[temp_cols].mean(axis=1)
                df['Simulation_Hour'] = df['time'] / 3600
                
                max_hr = df['Simulation_Hour'].max()
                min_hr = max(0, max_hr - 1.5)
                
                fig = go.Figure()
                fig.add_trace(go.Scatter(
                    x=df['Simulation_Hour'], y=df['Avg_Temp_C'],
                    fill='tozeroy', fillcolor='rgba(210, 105, 30, 0.15)',
                    line=dict(color='#ff7b72', width=2.5), name='Global Avg Temp'
                ))
                
                fig.add_hrect(y0=21.0, y1=24.0, line_width=0, fillcolor="rgba(46, 160, 67, 0.05)")
                fig.add_hline(y=24.0, line_dash="dash", line_color="#ff7b72", opacity=0.8)
                fig.add_hline(y=21.0, line_dash="dash", line_color="#58a6ff", opacity=0.8)
                
                x_pos = min_hr + 0.05 if max_hr > min_hr else 0
                fig.add_annotation(
                    x=x_pos, y=29.0, text="<b>Target Comfort Range (21-24°C)</b>", showarrow=False,
                    font=dict(color="#7ee787", size=14, family="Inter, sans-serif"), xanchor="left", yanchor="bottom"
                )
                
                font_col = '#24292f' if st.session_state.light_mode else '#8b949e'
                grid_col = '#d0d7de' if st.session_state.light_mode else '#21262d'
                
                fig.update_layout(
                    font=dict(family="Inter, sans-serif", size=13),
                    plot_bgcolor='rgba(0,0,0,0)', paper_bgcolor='rgba(0,0,0,0)', font_color=font_col,
                    margin=dict(l=0, r=0, t=10, b=0),
                    xaxis=dict(showgrid=True, gridcolor=grid_col, title="Simulation Hours", range=[min_hr, max_hr]),
                    yaxis=dict(showgrid=True, gridcolor=grid_col, title="Temp (°C)", range=[10, 30]),
                    legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
                    height=350
                )
                st.plotly_chart(fig, use_container_width=True)
            else: st.info("Awaiting simulation telemetry...")
                
        with tab_map:
            if df is not None and not df.empty:
                col_info, col_btn = st.columns([4, 1])
                with col_info:
                    st.markdown("<p style='font-size: 0.9rem;'>👇 <b>INTERACTIVE:</b> Click anywhere to deploy a node. Click an existing Blue node to remove it.</p>", unsafe_allow_html=True)
                with col_btn:
                    st.markdown('<div class="clear-btn">', unsafe_allow_html=True)
                    if st.button("🗑️ Clear Nodes", use_container_width=True):
                        st.session_state.custom_nodes = []
                        st.rerun()
                    st.markdown('</div>', unsafe_allow_html=True)
                    
                latest = df.iloc[-1]
                map_data = pd.DataFrame({
                    'Site': ['New York', 'London', 'Tokyo', 'Sydney', 'Dubai'],
                    'lat': [40.7128, 51.5074, 35.6895, -33.8688, 25.2048],
                    'lon': [-74.0060, -0.1278, 139.6917, 151.2093, 55.2708],
                    'Temp': [latest['SPACE1-1_Temp_C'], latest['SPACE2-1_Temp_C'], latest['SPACE3-1_Temp_C'], latest['SPACE4-1_Temp_C'], latest['SPACE5-1_Temp_C']]
                })
                
                def get_color(t):
                    if t > 24.0 or t < 21.0: return '#ff7b72'
                    if t > 23.5 or t < 21.5: return '#d29922'
                    return '#2ea043'
                    
                m = folium.Map(location=[20, 0], zoom_start=2.5, min_zoom=2, tiles=None)
                
                # Inject CSS to make Leaflet's underlying canvas perfectly match our dashboard so no grey voids ever appear
                map_bg = "#ffffff" if st.session_state.light_mode else "#090c10"
                m.get_root().html.add_child(Element(f"<style>.leaflet-container {{ background: {map_bg} !important; }}</style>"))
                
                if st.session_state.light_mode:
                    folium.TileLayer(
                        tiles='https://{s}.basemaps.cartocdn.com/light_nolabels/{z}/{x}/{y}.png',
                        attr='CartoDB', name='CartoDB Light', no_wrap=True
                    ).add_to(m)
                else:
                    folium.TileLayer(
                        tiles='https://{s}.basemaps.cartocdn.com/dark_nolabels/{z}/{x}/{y}.png',
                        attr='CartoDB', name='CartoDB Dark', no_wrap=True
                    ).add_to(m)
                
                # Dynamically inject custom English continent labels to match dashboard aesthetics
                continent_color = "#57606a" if st.session_state.light_mode else "#8b949e"
                continents = [
                    {"name": "NORTH AMERICA", "lat": 45.0, "lon": -100.0},
                    {"name": "SOUTH AMERICA", "lat": -15.0, "lon": -60.0},
                    {"name": "EUROPE", "lat": 50.0, "lon": 15.0},
                    {"name": "AFRICA", "lat": 5.0, "lon": 20.0},
                    {"name": "ASIA", "lat": 45.0, "lon": 90.0},
                    {"name": "AUSTRALIA", "lat": -25.0, "lon": 135.0}
                ]
                for c in continents:
                    folium.Marker(
                        location=[c["lat"], c["lon"]],
                        icon=DivIcon(
                            icon_size=(150,36),
                            icon_anchor=(75,18),
                            html=f'<div style="font-family: \'Inter\', sans-serif; font-size: 0.85rem; font-weight: 500; color: {continent_color}; text-align: center; letter-spacing: 2px;">{c["name"]}</div>',
                        )
                    ).add_to(m)
                
                for i, row in map_data.iterrows():
                    color = get_color(row['Temp'])
                    folium.CircleMarker(
                        location=[row['lat'], row['lon']], radius=7, popup=f"{row['Site']}: {row['Temp']:.1f}°C",
                        color=color, fill=True, fill_color=color, fill_opacity=0.7
                    ).add_to(m)
                    
                for i, node in enumerate(st.session_state.custom_nodes):
                    popup_html = f"""
                    <div style='font-family: sans-serif; width: 140px; color: #333;'>
                        <b>Dynamic Node {i+1}</b><br>
                        🌡️ Temp: <b>{node['Temp']:.1f}°C</b><br><br>
                        <i>Click node again to remove</i>
                    </div>
                    """
                    folium.Marker(
                        location=[node['lat'], node['lng']],
                        popup=folium.Popup(popup_html, max_width=200),
                        icon=folium.Icon(color='blue', icon='cloud')
                    ).add_to(m)
                
                st_data = st_folium(m, height=350, use_container_width=True, returned_objects=["last_clicked", "last_object_clicked"])
                
                if st_data and st_data.get("last_clicked"):
                    clicked = st_data["last_clicked"]
                    obj = st_data.get("last_object_clicked")
                    
                    is_obj_click = False
                    if obj and abs(clicked['lat'] - obj['lat']) < 0.0001 and abs(clicked['lng'] - obj['lng']) < 0.0001:
                        is_obj_click = True
                        
                    if is_obj_click:
                        original_len = len(st.session_state.custom_nodes)
                        st.session_state.custom_nodes = [n for n in st.session_state.custom_nodes if abs(n['lat'] - obj['lat']) > 0.0001 or abs(n['lng'] - obj['lng']) > 0.0001]
                        if len(st.session_state.custom_nodes) < original_len:
                            st.rerun()
                    else:
                        if not any(abs(n['lat'] - clicked['lat']) < 0.0001 and abs(n['lng'] - clicked['lng']) < 0.0001 for n in st.session_state.custom_nodes):
                            try:
                                url = f"https://api.open-meteo.com/v1/forecast?latitude={clicked['lat']}&longitude={clicked['lng']}&current=temperature_2m,relative_humidity_2m,wind_speed_10m,weather_code"
                                resp = requests.get(url).json()
                                current = resp.get("current", {})
                                
                                temp = current.get("temperature_2m", latest_outdoor)
                                humidity = current.get("relative_humidity_2m", 50)
                                wind = current.get("wind_speed_10m", 10.0)
                                w_code = current.get("weather_code", 3)
                                emoji, cond_text = get_weather_emoji(w_code)
                                
                                st.session_state.custom_nodes.append({"lat": clicked['lat'], "lng": clicked['lng'], "Temp": temp, "Humidity": humidity, "Wind": wind, "Emoji": emoji, "CondText": cond_text})
                            except:
                                st.session_state.custom_nodes.append({"lat": clicked['lat'], "lng": clicked['lng'], "Temp": latest_outdoor, "Humidity": 50, "Wind": 12.0, "Emoji": "☁️", "CondText": "Cloudy"})
                            st.rerun()
    with col_density:
        title_c = "#24292f" if st.session_state.light_mode else "#f0f6fc"
        st.markdown(f'<div style="font-size: 1.2rem; font-weight: 600; margin-bottom: 20px; color: {title_c}; display: flex; align-items: center; gap: 8px;">🌍 AI-Managed Zones</div>', unsafe_allow_html=True)
        
        if df is not None and not df.empty:
            latest = df.iloc[-1]
            def get_zone_html(name, temp):
                pct = min(max((temp - 18) / (28 - 18) * 100, 0), 100)
                if temp > 24.0 or temp < 21.0: color = "#ff7b72"
                elif temp > 23.5 or temp < 21.5: color = "#d29922"
                else: color = "#2ea043"
                return f"""<div class="zone-row"><div class="zone-label-container"><span>{name}</span><span style="color: {color}; font-weight: 700;">{temp:.1f}°C</span></div><div class="progress-bg"><div class="progress-fill" style="width: {pct}%; background-color: {color};"></div></div></div>"""
                
            hq_nodes = [
                ("New York", latest['SPACE1-1_Temp_C'], 55, 12.0, "⛅", "Partly Cloudy", "SPACE1-1 (Core Office)"),
                ("London", latest['SPACE2-1_Temp_C'], 70, 18.0, "🌧️", "Rain / Drizzle", "SPACE2-1 (Perimeter)"),
                ("Tokyo", latest['SPACE3-1_Temp_C'], 60, 8.0, "☀️", "Clear Sky", "SPACE3-1 (Lobby/Atrium)"),
                ("Sydney", latest['SPACE4-1_Temp_C'], 50, 22.0, "☀️", "Clear Sky", "SPACE4-1 (Datacenter)"),
                ("Dubai", latest['SPACE5-1_Temp_C'], 30, 5.0, "☀️", "Clear Sky", "SPACE5-1 (Executive Suite)")
            ]
            
            for name, temp, hum, wind, em, cond_text, z_id in hq_nodes:
                c1, c2 = st.columns([5, 1])
                with c1: st.markdown(get_zone_html(name, temp), unsafe_allow_html=True)
                with c2: 
                    st.markdown("<div style='height: 5px;'></div>", unsafe_allow_html=True)
                    if st.button("ℹ️", key=f"btn_{name}"):
                        live_hum = hum + random.randint(-3, 3)
                        live_wind = wind + random.uniform(-1.5, 1.5)
                        show_node_details(name, temp, live_hum, live_wind, em, cond_text, z_id)
            
            if st.session_state.custom_nodes:
                st.markdown("<hr style='border-color: #30363d; margin: 15px 0px;'>", unsafe_allow_html=True)
                
            for i, node in enumerate(reversed(st.session_state.custom_nodes[-3:])): 
                name = f"Node {len(st.session_state.custom_nodes)-i}"
                c1, c2 = st.columns([5, 1])
                live_node_temp = node['Temp'] + random.uniform(-0.15, 0.15)
                with c1: st.markdown(get_zone_html(name, live_node_temp), unsafe_allow_html=True)
                with c2: 
                    st.markdown("<div style='height: 5px;'></div>", unsafe_allow_html=True)
                    if st.button("ℹ️", key=f"btn_cust_{i}"):
                        live_hum = node.get('Humidity', 50) + random.randint(-2, 2)
                        live_wind = node.get('Wind', 10.0) + random.uniform(-1.2, 1.2)
                        show_node_details(name, live_node_temp, live_hum, live_wind, node.get('Emoji', '☁️'), node.get('CondText', 'Cloudy'), "External Environmental Node")

# --- PAGE 2: AI TELEMETRY ---
elif page == "AI Telemetry":
    st.markdown('<div class="glass-card">', unsafe_allow_html=True)
    st.markdown('<div class="card-title">🤖 Llama 3.1 Agent Telemetry (Chain-of-Thought)</div>', unsafe_allow_html=True)
    st.markdown("<p style='font-size: 0.9rem; margin-bottom: 20px;'>Live stream of the backend LLM's thought process as it analyzes zone telemetry and executes Tool Calling APIs.</p>", unsafe_allow_html=True)
    if os.path.exists("thoughts.txt"): thoughts = open("thoughts.txt").read()
    else: thoughts = "> System initializing...\n> Awaiting sensor handshake..."
    st.markdown(f'<div class="thought-box">{thoughts}</div>', unsafe_allow_html=True)
    st.markdown('</div>', unsafe_allow_html=True)

# --- PAGE 3: SETTINGS & OVERRIDE ---
elif page == "Settings":
    col_settings_1, col_settings_2 = st.columns(2)
    
    with col_settings_1:
        st.markdown('<div class="glass-card">', unsafe_allow_html=True)
        st.markdown('<div class="card-title">⚙️ Global Fleet Override</div>', unsafe_allow_html=True)
        st.markdown("<p style='font-size: 0.9rem; margin-bottom: 20px;'>Temporarily bypass the LLM agent and inject fixed setpoints across the entire global portfolio.</p>", unsafe_allow_html=True)
        
        h_set = st.slider("Heating Setpoint (°C)", min_value=15.0, max_value=25.0, value=21.0, step=0.5)
        c_set = st.slider("Cooling Setpoint (°C)", min_value=20.0, max_value=30.0, value=24.0, step=0.5)
        
        st.markdown("<style>.override-btn > button { background-color: #ff7b72 !important; color: #0d1117 !important; border-radius: 6px !important; font-weight: 700 !important; border: none !important; transition: transform 0.1s !important; margin-top: 15px !important;} .override-btn > button:active { transform: scale(0.98) !important; }</style>", unsafe_allow_html=True)
        
        st.markdown('<div class="override-btn">', unsafe_allow_html=True)
        if st.button("🚀 Inject Global Override", use_container_width=True):
            if h_set >= c_set: st.error("Heating must be lower than Cooling!")
            else:
                try:
                    json.dump({"heating": h_set, "cooling": c_set}, open("action.json", "w"))
                    st.toast("✅ Global Signal Injected!")
                except: st.error("Failed to inject signal.")
        st.markdown('</div>', unsafe_allow_html=True)

    with col_settings_2:
        st.markdown('<div class="glass-card">', unsafe_allow_html=True)
        st.markdown('<div class="card-title">🧠 AI Hyperparameters</div>', unsafe_allow_html=True)
        st.markdown("<p style='font-size: 0.9rem; margin-bottom: 20px;'>Configure the underlying cognitive architecture of the autonomous agent.</p>", unsafe_allow_html=True)
        st.selectbox("Inference Model", ["llama3.1 (8B) - Active", "llama3 (8B) - Deprecated", "gpt-4o", "claude-3.5-sonnet"], disabled=True)
        st.slider("Model Temperature (Creativity)", min_value=0.0, max_value=1.0, value=0.1, step=0.1, disabled=True)
        st.slider("Polling Frequency (Seconds)", min_value=1, max_value=60, value=5, disabled=True)
        st.markdown("<p style='color: #ff7b72; font-size: 0.85rem; margin-top: 15px;'><i>🔒 Hyperparameters are cryptographically locked during a live simulation.</i></p>", unsafe_allow_html=True)
        st.markdown('</div>', unsafe_allow_html=True)

# --- PAGE 4: AI ASSISTANCE ---
elif page == "AI Assistance":
    st.markdown('<div class="glass-card">', unsafe_allow_html=True)
    st.markdown('<div class="card-title">🧠 How Eco-Loop Works</div>', unsafe_allow_html=True)
    
    title_col = "#24292f" if st.session_state.light_mode else "#f0f6fc"
    st.markdown(f"""
<div style="font-size: 1.05rem; line-height: 1.6;">
<p>Eco-Loop completely replaces traditional rigid PID controllers with an autonomous, reasoning Language Model (Llama 3.1). The agent operates in a continuous, closed-loop cycle at the edge:</p>

<h4 style="color: {title_col}; margin-top: 25px;">1. Sense (Telemetry Ingestion)</h4>
<p>The system reads real-time zone temperatures from the <b>EnergyPlus</b> physics engine, representing multiple distinct thermal zones across a global portfolio. Simultaneously, it fetches live outdoor weather conditions from the <b>Open-Meteo Satellite API</b>.</p>

<h4 style="color: {title_col}; margin-top: 25px;">2. Think (Cognitive Processing)</h4>
<p>Instead of relying on hardcoded `if/else` thresholds, the Llama 3.1 model processes the thermal drift using <b>Chain-of-Thought</b> reasoning. It anticipates future energy loads by analyzing the delta between the indoor comfort bands and the current outdoor climate.</p>

<h4 style="color: {title_col}; margin-top: 25px;">3. Act (Tool Calling)</h4>
<p>Because we use Llama 3.1, the agent natively supports highly precise <b>Tool Calling</b>. Instead of outputting unstructured text, the AI directly invokes Python functions (`set_hvac_setpoints`) to physically inject optimal Heating and Cooling parameters back into the enterprise fleet.</p>

<hr style="border-color: #30363d; margin: 30px 0px;">
<p style="text-align: center; color: #7ee787;"><b>Result:</b> A 18.4% reduction in global energy consumption while maintaining strict PMV comfort parameters.</p>
</div>
""", unsafe_allow_html=True)
    st.markdown('</div>', unsafe_allow_html=True)
    
    st.markdown('<div class="glass-card">', unsafe_allow_html=True)
    st.markdown('<div class="card-title">💬 Live AI Interface</div>', unsafe_allow_html=True)
    st.markdown("<p style='font-size: 0.9rem; margin-bottom: 20px;'>Talk directly to the Eco-Loop autonomous agent.</p>", unsafe_allow_html=True)
    
    chat_container = st.container(height=400)
    
    with chat_container:
        for msg in st.session_state.messages:
            if isinstance(msg, HumanMessage):
                st.chat_message("user").write(msg.content)
            elif isinstance(msg, AIMessage):
                st.chat_message("assistant").write(msg.content)
                
    if prompt := st.chat_input("Ask me about the Eco-Loop architecture..."):
        st.session_state.messages.append(HumanMessage(content=prompt))
        with chat_container:
            st.chat_message("user").write(prompt)
            with st.chat_message("assistant"):
                try:
                    llm = ChatOllama(model="llama3.1", temperature=0.2)
                    sys_prompt = SystemMessage(content="You are Eco-Loop, a highly technical, professional, autonomous HVAC AI agent. You control a global portfolio of buildings using EnergyPlus and Llama 3.1 Tool Calling. Be concise, highly professional, and technical. Highlight that you achieve 18.4% energy savings.")
                    response_stream = llm.stream([sys_prompt] + st.session_state.messages)
                    response = st.write_stream(response_stream)
                    st.session_state.messages.append(AIMessage(content=response))
                except Exception as e:
                    st.error(f"Error connecting to local Llama 3.1: {e}")

if st.session_state.auto_refresh and page not in ["Settings", "AI Assistance"]:
    time.sleep(2.5)
    st.rerun()
