import os
import json
import streamlit as st

SAVES_DIR = "saves"

def ensure_saves_dir():
    if not os.path.exists(SAVES_DIR):
        os.makedirs(SAVES_DIR)

def list_saves():
    ensure_saves_dir()
    files = [f for f in os.listdir(SAVES_DIR) if f.endswith(".json")]
    return [os.path.splitext(f)[0] for f in files]

def get_default_save_data(save_name):
    return {
        "save_name": save_name,
        "nodes": [],          # Buildings: [{"id": "Building A", "name": "Building A"}]
        "edges": [],          # Distances: [{"from": "Building A", "to": "Building B", "distance": 150}]
        "mst_edges": [],      # Output of MST calculation
        "rooms": [],          # Rooms: [{"building": "Building A", "name": "Room 101", "capacity": 50, "usage": "Anatomy Only"}]
        "custom_specs": [],   # Custom room usage specifications
        "majors": [],         # Majors: [{"name": "Medicine", "students": 40}]
        "lecturers": [],      # Lecturers: [{"id": "lect_01", "name": "Dr. Somchai", "department": "Radiological Technology"}]
        "subjects": [],       # Subjects: [{"id": "subj_01", "code": "MED101", "name": "Anatomy I", "majors": ["Medicine"], "hours_per_period": 2, "required_usage": "General Lecture", "lecturer": "Unassigned"}]
        "breaks": [],         # Breaks: [{"name": "Lunch Break", "days": ["Monday", "Tuesday"], "start_time": "12:00", "end_time": "13:00"}]
        "timetable": {}       # Generated schedule output
    }

def save_data_to_file(save_name, data):
    ensure_saves_dir()
    filepath = os.path.join(SAVES_DIR, f"{save_name}.json")
    with open(filepath, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=4, ensure_ascii=False)

def load_data_from_file(save_name):
    ensure_saves_dir()
    filepath = os.path.join(SAVES_DIR, f"{save_name}.json")
    if os.path.exists(filepath):
        with open(filepath, "r", encoding="utf-8") as f:
            data = json.load(f)
            data.setdefault("custom_specs", [])
            data.setdefault("lecturers", [])
            data.setdefault("nodes", [])
            data.setdefault("edges", [])
            data.setdefault("rooms", [])
            data.setdefault("majors", [])
            data.setdefault("subjects", [])
            data.setdefault("breaks", [])
            data.setdefault("timetable", {})
            return data
    return get_default_save_data(save_name)

def delete_save_file(save_name):
    ensure_saves_dir()
    filepath = os.path.join(SAVES_DIR, f"{save_name}.json")
    if os.path.exists(filepath):
        os.remove(filepath)

def apply_custom_css():
    theme = st.session_state.get("app_theme", "🌌 Midnight Glassmorphism")

    if theme == "🔮 Deep Violet Cyberpunk":
        app_bg = "radial-gradient(circle at 10% 20%, #090314 0%, #18092B 35%, #2E1065 80%, #05010A 100%) !important;"
        card_bg = "rgba(24, 9, 43, 0.78) !important;"
        card_border = "1px solid rgba(192, 132, 252, 0.2) !important;"
        accent_color = "#E087FF"
        btn_bg = "linear-gradient(135deg, #9333EA 0%, #C084FC 100%) !important;"
        btn_hover = "linear-gradient(135deg, #7E22CE 0%, #A855F7 100%) !important;"
        title_grad = "linear-gradient(135deg, #FFFFFF 0%, #E087FF 60%, #C084FC 100%);"
    elif theme == "🌊 Emerald Cyber-Deck":
        app_bg = "radial-gradient(circle at 10% 20%, #02120D 0%, #062C22 35%, #064E3B 80%, #010A07 100%) !important;"
        card_bg = "rgba(6, 44, 34, 0.78) !important;"
        card_border = "1px solid rgba(52, 211, 153, 0.2) !important;"
        accent_color = "#34D399"
        btn_bg = "linear-gradient(135deg, #059669 0%, #10B981 100%) !important;"
        btn_hover = "linear-gradient(135deg, #047857 0%, #059669 100%) !important;"
        title_grad = "linear-gradient(135deg, #FFFFFF 0%, #34D399 60%, #6EE7B7 100%);"
    elif theme == " Pearl Silver":
        app_bg = "linear-gradient(135deg, #E2E8F0 0%, #F1F5F9 50%, #CBD5E1 100%) !important;"
        card_bg = "#FFFFFF !important;"
        card_border = "1px solid #CBD5E1 !important;"
        accent_color = "#2563EB"
        btn_bg = "linear-gradient(135deg, #0F172A 0%, #1E293B 100%) !important;"
        btn_hover = "linear-gradient(135deg, #1E293B 0%, #334155 100%) !important;"
        title_grad = "linear-gradient(135deg, #0F172A 0%, #2563EB 100%);"
    else:  # Default: 🌌 Midnight Glassmorphism
        app_bg = "radial-gradient(circle at 10% 20%, #0B0F19 0%, #0F172A 35%, #1E1B4B 80%, #030712 100%) !important;"
        card_bg = "rgba(15, 23, 42, 0.78) !important;"
        card_border = "1px solid rgba(255, 255, 255, 0.12) !important;"
        accent_color = "#38BDF8"
        btn_bg = "linear-gradient(135deg, #2563EB 0%, #4F46E5 100%) !important;"
        btn_hover = "linear-gradient(135deg, #1D4ED8 0%, #4338CA 100%) !important;"
        title_grad = "linear-gradient(135deg, #FFFFFF 0%, #38BDF8 60%, #818CF8 100%);"

    is_light = (theme == " Pearl Silver")
    text_main = "#0F172A" if is_light else "#F8FAFC"
    text_sub = "#475569" if is_light else "#94A3B8"
    input_bg = "#FFFFFF" if is_light else "rgba(30, 41, 59, 0.85)"
    input_border = "#CBD5E1" if is_light else "rgba(148, 163, 184, 0.3)"

    css = f"""<style>
@import url('https://fonts.googleapis.com/css2?family=Prompt:wght@300;400;500;600;700&display=swap');

@font-face {{
    font-family: 'Chulabhorn Likit Text';
    src: local('Chulabhorn Likit Text'), local('ChulabhornLikitText');
    font-weight: normal;
    font-style: normal;
}}

/* Base Theme Styling */
.stApp {{
    background: {app_bg}
    background-attachment: fixed !important;
    color: {text_main} !important;
    font-family: 'Chulabhorn Likit Text', 'Prompt', -apple-system, BlinkMacSystemFont, sans-serif;
}}

/* Sidebar Custom Styling */
[data-testid="stSidebar"] {{
    background: {'rgba(248, 250, 252, 0.95)' if is_light else 'rgba(11, 15, 25, 0.92)'} !important;
    backdrop-filter: blur(16px) !important;
    border-right: 1px solid {'#E2E8F0' if is_light else 'rgba(255, 255, 255, 0.08)'} !important;
}}

[data-testid="stSidebar"] * {{
    color: {text_main} !important;
}}

/* Clean Top Badge */
.brand-badge {{
    display: inline-block;
    background: {'rgba(241, 245, 249, 0.9)' if is_light else 'rgba(30, 41, 59, 0.8)'};
    color: {accent_color};
    border: 1px solid {'#CBD5E1' if is_light else 'rgba(56, 189, 248, 0.3)'};
    font-size: 0.85rem;
    font-weight: 600;
    letter-spacing: 0.05em;
    padding: 6px 16px;
    border-radius: 9999px;
    margin-bottom: 12px;
    font-family: 'Chulabhorn Likit Text', 'Prompt', sans-serif;
    box-shadow: {'0 2px 8px rgba(0,0,0,0.05)' if is_light else '0 0 12px rgba(56, 189, 248, 0.15)'};
}}

.schedpath-title {{
    font-size: 3rem;
    font-weight: 800;
    letter-spacing: -0.02em;
    line-height: 1.15;
    margin-bottom: 8px;
    font-family: 'Chulabhorn Likit Text', 'Prompt', sans-serif;
    background: {title_grad}
    -webkit-background-clip: text;
    -webkit-text-fill-color: transparent;
}}

.schedpath-subtitle {{
    font-size: 1.1rem;
    font-weight: 400;
    color: {text_sub} !important;
    -webkit-text-fill-color: {text_sub} !important;
    margin-bottom: 24px;
    line-height: 1.6;
    font-family: 'Chulabhorn Likit Text', 'Prompt', sans-serif;
}}

/* Glassmorphism / Clean Card Container */
.clean-card, .clean-card-slate {{
    background: {card_bg}
    backdrop-filter: blur(16px) !important;
    border: {card_border}
    box-shadow: {'0 10px 30px rgba(15, 23, 42, 0.05)' if is_light else '0 20px 45px rgba(0, 0, 0, 0.5)'} !important;
    border-radius: 24px !important;
    padding: 28px !important;
    margin-bottom: 24px !important;
    color: {text_main} !important;
}}

.clean-card *, .clean-card-slate * {{
    color: {text_main};
}}

/* Feature pill list */
.feature-item {{
    display: flex;
    align-items: center;
    gap: 12px;
    margin-bottom: 14px;
    font-size: 0.95rem;
    color: {text_main};
}}

.feature-icon {{
    width: 30px;
    height: 30px;
    border-radius: 50%;
    background: {'#F1F5F9' if is_light else 'rgba(30, 41, 59, 0.9)'};
    border: 1px solid {'#E2E8F0' if is_light else 'rgba(56, 189, 248, 0.3)'};
    color: {accent_color};
    display: flex;
    align-items: center;
    justify-content: center;
    font-weight: bold;
    font-size: 0.85rem;
}}

/* Streamlit Buttons */
div.stButton > button {{
    background: {btn_bg}
    color: #FFFFFF !important;
    border: none !important;
    border-radius: 9999px !important;
    font-weight: 600 !important;
    font-size: 0.95rem !important;
    padding: 0.65rem 2rem !important;
    transition: all 0.25s ease !important;
    box-shadow: {'0 4px 14px rgba(15, 23, 42, 0.15)' if is_light else '0 4px 20px rgba(37, 99, 235, 0.35)'} !important;
    font-family: 'Chulabhorn Likit Text', 'Prompt', sans-serif !important;
}}

div.stButton > button:hover {{
    background: {btn_hover}
    color: #FFFFFF !important;
    transform: translateY(-2px) !important;
    box-shadow: {'0 8px 22px rgba(15, 23, 42, 0.25)' if is_light else '0 8px 28px rgba(37, 99, 235, 0.5)'} !important;
}}

/* Secondary Buttons */
div.stButton > button[data-testid="baseButton-secondary"] {{
    background: {'#FEF2F2' if is_light else 'rgba(239, 68, 68, 0.18)'} !important;
    color: {'#DC2626' if is_light else '#FCA5A5'} !important;
    border: 1px solid {'#FCA5A5' if is_light else 'rgba(239, 68, 68, 0.4)'} !important;
    box-shadow: none !important;
}}

div.stButton > button[data-testid="baseButton-secondary"]:hover {{
    background: {'#DC2626' if is_light else '#EF4444'} !important;
    color: #FFFFFF !important;
}}

/* Input Fields & Selectboxes */
.stTextInput input, .stSelectbox div[data-baseweb="select"], .stNumberInput input, .stMultiSelect div[data-baseweb="select"] {{
    border-radius: 14px !important;
    border: 1px solid {input_border} !important;
    background-color: {input_bg} !important;
    color: {text_main} !important;
    padding: 0.5rem 1rem !important;
    font-family: 'Chulabhorn Likit Text', 'Prompt', sans-serif !important;
}}

/* Tabs Customization */
.stTabs [data-baseweb="tab-list"] {{
    background-color: {'rgba(241, 245, 249, 0.8)' if is_light else 'rgba(15, 23, 42, 0.8)'} !important;
    border-radius: 16px !important;
    padding: 4px !important;
    border: 1px solid {'#CBD5E1' if is_light else 'rgba(255, 255, 255, 0.1)'} !important;
}}

.stTabs [data-baseweb="tab"] {{
    color: {text_sub} !important;
    font-weight: 600 !important;
    border-radius: 12px !important;
    padding: 8px 16px !important;
}}

.stTabs [aria-selected="true"] {{
    background: {btn_bg}
    color: #FFFFFF !important;
}}

/* Metrics */
[data-testid="stMetricValue"] {{
    color: {accent_color} !important;
    font-weight: 800 !important;
}}

[data-testid="stMetricLabel"] {{
    color: {text_sub} !important;
}}
</style>"""
    st.markdown(css, unsafe_allow_html=True)


def render_intro_screen():
    apply_custom_css()
    
    st.write("")
    col1, col2 = st.columns([1.25, 1])
    
    with col1:
        st.markdown('<div class="brand-badge">🎓 Chulabhorn Royal Academy</div>', unsafe_allow_html=True)
        st.markdown('<div class="schedpath-title">A Clean Start for Schedule Planning</div>', unsafe_allow_html=True)
        st.markdown(
            '<div class="schedpath-subtitle">'
            'SCHEDPATH uses Minimum Spanning Tree (MST) graph algorithms to optimize campus building routes, '
            'room allocations, lecturer workloads, and major timetables for lecturers and students.'
            '</div>', 
            unsafe_allow_html=True
        )
        
        st.markdown("""<div class="clean-card">
<h4 style="margin-top:0; margin-bottom: 18px; font-weight:700;">System Capabilities</h4>
<div class="feature-item">
<div class="feature-icon">1</div>
<div><b>Campus Network & MST:</b> Connect building nodes & minimize student walking distances</div>
</div>
<div class="feature-item">
<div class="feature-icon">2</div>
<div><b>Smart Room Allocator:</b> Custom room specs, capacities & specialized usages</div>
</div>
<div class="feature-item">
<div class="feature-icon">3</div>
<div><b>Faculty & Timetable Generator:</b> Non-overlapping lecturer schedules & break slots</div>
</div>
</div>""", unsafe_allow_html=True)
        
        st.write("")
        bcol1, bcol2 = st.columns([1.2, 1])
        with bcol1:
            if st.button("Start Application →", use_container_width=True):
                st.session_state.file1_subpage = "save_select"
                st.rerun()
        with bcol2:
            if st.button("📜 Version Log (v2.0)", type="secondary", use_container_width=True):
                st.session_state.current_page = "vlog"
                st.rerun()
            
    with col2:
        st.markdown("""<div class="clean-card-slate" style="text-align: center; height: 100%; min-height: 380px; display: flex; flex-direction: column; justify-content: center; align-items: center;">
<svg width="200" height="200" viewBox="0 0 200 200" fill="none" xmlns="http://www.w3.org/2000/svg">
<circle cx="100" cy="100" r="85" fill="#1E293B" opacity="0.8"/>
<circle cx="100" cy="100" r="60" stroke="#38BDF8" stroke-width="2" stroke-dasharray="6 6"/>
<line x1="60" y1="60" x2="140" y2="70" stroke="#64748B" stroke-width="3"/>
<line x1="140" y1="70" x2="150" y2="140" stroke="#64748B" stroke-width="3"/>
<line x1="60" y1="60" x2="70" y2="135" stroke="#64748B" stroke-width="3"/>
<line x1="70" y1="135" x2="150" y2="140" stroke="#64748B" stroke-width="3"/>
<line x1="60" y1="60" x2="140" y2="70" stroke="#EF4444" stroke-width="4" stroke-linecap="round"/>
<circle cx="60" cy="60" r="14" fill="#0F172A" stroke="#38BDF8" stroke-width="2"/>
<circle cx="140" cy="70" r="14" fill="#0F172A" stroke="#38BDF8" stroke-width="2"/>
<circle cx="150" cy="140" r="14" fill="#0F172A" stroke="#38BDF8" stroke-width="2"/>
<circle cx="70" cy="135" r="14" fill="#0F172A" stroke="#38BDF8" stroke-width="2"/>
<text x="60" y="64" fill="white" font-size="10" font-weight="bold" text-anchor="middle">A</text>
<text x="140" y="74" fill="white" font-size="10" font-weight="bold" text-anchor="middle">B</text>
<text x="150" y="144" fill="white" font-size="10" font-weight="bold" text-anchor="middle">C</text>
<text x="70" y="139" fill="white" font-size="10" font-weight="bold" text-anchor="middle">D</text>
</svg>
<h3 style="margin-top: 16px; margin-bottom: 4px; font-weight: 800;">SCHEDPATH</h3>
<p style="font-size: 0.9rem; margin: 0; opacity: 0.8;">Constraint-Based MST Scheduling Engine</p>
</div>""", unsafe_allow_html=True)


def render_save_select():
    apply_custom_css()
    
    st.write("")
    st.markdown('<div class="brand-badge">📁 Step 1 | Save File Workspace</div>', unsafe_allow_html=True)
    st.markdown('<div class="schedpath-title">Workspace Selection</div>', unsafe_allow_html=True)
    st.markdown('<div class="schedpath-subtitle">Create a new workspace or load an existing project file to configure campus maps and schedules.</div>', unsafe_allow_html=True)
    
    col_new, col_load = st.columns([1, 1])
    
    with col_new:
        st.markdown('<div class="clean-card">', unsafe_allow_html=True)
        st.subheader("✨ Create New Workspace")
        st.write("Start fresh with empty campus buildings, rooms, lecturers, and subject definitions.")
        
        new_save_name = st.text_input("New Workspace Name:", placeholder="e.g. CRA_Schedule_2026", key="new_save_input")
        
        if st.button("➕ Create Workspace", use_container_width=True):
            save_str = new_save_name.strip()
            if not save_str:
                st.error("Please enter a valid workspace name.")
            else:
                existing_saves = list_saves()
                if save_str in existing_saves:
                    st.error(f"Workspace '{save_str}' already exists! Choose another name or load it on the right.")
                else:
                    new_data = get_default_save_data(save_str)
                    save_data_to_file(save_str, new_data)
                    st.session_state.active_save = save_str
                    st.session_state.save_data = new_data
                    st.toast(f"Created & loaded new workspace '{save_str}'!", icon="✨")
                    st.success(f"Created new workspace '{save_str}'. Proceeding to Step 2...")
                    st.session_state.current_page = "file2"
                    st.rerun()
                    
        st.markdown('</div>', unsafe_allow_html=True)
        
    with col_load:
        st.markdown('<div class="clean-card">', unsafe_allow_html=True)
        st.subheader("📂 Load Saved Workspace")
        st.write("Continue working on a previously configured campus workspace.")
        
        existing_saves = list_saves()
        
        if existing_saves:
            selected_save = st.selectbox("Select Active Workspace:", existing_saves, key="select_save_dropdown")
            
            btn_col1, btn_col2 = st.columns([2, 1])
            
            with btn_col1:
                if st.button("🚀 Load & Proceed to Step 2", use_container_width=True):
                    data = load_data_from_file(selected_save)
                    st.session_state.active_save = selected_save
                    st.session_state.save_data = data
                    st.toast(f"Loaded workspace '{selected_save}'!", icon="📂")
                    st.session_state.current_page = "file2"
                    st.rerun()
                    
            with btn_col2:
                if st.button("🗑️ Delete", type="secondary", use_container_width=True):
                    delete_save_file(selected_save)
                    if st.session_state.active_save == selected_save:
                        st.session_state.active_save = None
                        st.session_state.save_data = None
                    st.toast(f"Deleted workspace '{selected_save}'.", icon="🗑️")
                    st.warning(f"Deleted workspace '{selected_save}'.")
                    st.rerun()
        else:
            st.info("No saved workspaces found. Create your first workspace on the left!")
            
        st.markdown('</div>', unsafe_allow_html=True)


def render():
    if "file1_subpage" not in st.session_state:
        st.session_state.file1_subpage = "intro"
        
    if st.session_state.file1_subpage == "intro":
        render_intro_screen()
    else:
        render_save_select()
