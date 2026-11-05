import streamlit as st
import file1
import file2
import file3
import file4

# Page Configuration
st.set_page_config(
    page_title="SCHEDPATH - MST Scheduler",
    page_icon="🗺️",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Initialize Session State Variables
if "current_page" not in st.session_state:
    st.session_state.current_page = "file1"

if "active_save" not in st.session_state:
    st.session_state.active_save = None

if "save_data" not in st.session_state:
    st.session_state.save_data = None

if "app_theme" not in st.session_state:
    st.session_state.app_theme = "🌌 Midnight Glassmorphism"

# Sidebar Navigation / Progress Indicator
with st.sidebar:
    st.markdown("<h2 style='text-align: center; font-weight: 800;'>SCHEDPATH</h2>", unsafe_allow_html=True)
    st.markdown("<p style='text-align: center; font-size: 0.82rem; font-weight: 600; opacity: 0.8;'>CONNECTING ALL THE DOTS</p>", unsafe_allow_html=True)
    st.divider()

    # Theme Selector Feature
    st.subheader("🎨 Theme Settings")
    theme_options = [
        "🌌 Midnight Glassmorphism", 
        "🔮 Deep Violet Cyberpunk", 
        "🌊 Emerald Cyber-Deck", 
        " Pearl Silver"
    ]
    
    if st.session_state.get("app_theme_select") not in theme_options:
        st.session_state["app_theme_select"] = st.session_state.app_theme

    selected_theme = st.selectbox(
        "Choose Background Style:",
        theme_options,
        key="app_theme_select"
    )
    if selected_theme != st.session_state.app_theme:
        st.session_state.app_theme = selected_theme
        st.rerun()

    st.divider()
    
    if st.session_state.active_save:
        st.info(f"📁 **Active Save:** `{st.session_state.active_save}`")
    else:
        st.warning("⚠️ No active save file selected")
        
    st.subheader("📌 Workflow Stepper")
    
    step1_style = "👉 " if st.session_state.current_page == "file1" else "  "
    step2_style = "👉 " if st.session_state.current_page == "file2" else "  "
    step3_style = "👉 " if st.session_state.current_page == "file3" else "  "
    step4_style = "👉 " if st.session_state.current_page == "file4" else "  "
    vlog_style = "👉 " if st.session_state.current_page == "vlog" else "  "

    if st.button(f"{step1_style} 1. Workspace Selection", use_container_width=True):
        st.session_state.current_page = "file1"
        st.rerun()
        
    if st.button(f"{step2_style} 2. Map & Room Specs", use_container_width=True, disabled=not st.session_state.active_save):
        st.session_state.current_page = "file2"
        st.rerun()

    if st.button(f"{step3_style} 3. Curriculum & Faculty", use_container_width=True, disabled=not st.session_state.active_save):
        st.session_state.current_page = "file3"
        st.rerun()

    if st.button(f"{step4_style} 4. Timetable & Transit", use_container_width=True, disabled=not st.session_state.active_save):
        st.session_state.current_page = "file4"
        st.rerun()

    st.divider()
    if st.button(f"{vlog_style} 📜 System Version Log", use_container_width=True):
        st.session_state.current_page = "vlog"
        st.rerun()

# Apply Theme CSS globally
file1.apply_custom_css()

# Top Visual Stepper & Dynamic KPI Header
if st.session_state.active_save and st.session_state.save_data and st.session_state.current_page != "vlog":
    data = st.session_state.save_data
    
    nodes_cnt = len(data.get("nodes", []))
    rooms_cnt = len(data.get("rooms", []))
    cap_total = sum(r.get("capacity", 0) for r in data.get("rooms", []))
    majors_cnt = len(data.get("majors", []))
    lects_cnt = len(data.get("lecturers", []))
    subjs_cnt = len(data.get("subjects", []))
    mst_edges = data.get("mst_edges", [])
    mst_dist = sum(float(e.get("distance", 0)) for e in mst_edges)
    
    curr = st.session_state.current_page
    theme = st.session_state.app_theme
    is_light = (theme == " Pearl Silver")

    active_bg = "linear-gradient(135deg, #2563EB 0%, #4F46E5 100%)" if not is_light else "#0F172A"
    inactive_bg = "rgba(30, 41, 59, 0.7)" if not is_light else "#E2E8F0"
    active_fg = "#FFFFFF"
    inactive_fg = "#94A3B8" if not is_light else "#475569"

    s1_bg = active_bg if curr == "file1" else inactive_bg
    s1_fg = active_fg if curr == "file1" else inactive_fg
    s2_bg = active_bg if curr == "file2" else inactive_bg
    s2_fg = active_fg if curr == "file2" else inactive_fg
    s3_bg = active_bg if curr == "file3" else inactive_bg
    s3_fg = active_fg if curr == "file3" else inactive_fg
    s4_bg = active_bg if curr == "file4" else inactive_bg
    s4_fg = active_fg if curr == "file4" else inactive_fg

    stepper_bg = "rgba(15, 23, 42, 0.78)" if not is_light else "#FFFFFF"
    stepper_border = "rgba(255, 255, 255, 0.12)" if not is_light else "#CBD5E1"

    stepper_html = f"""
    <div style="background: {stepper_bg}; backdrop-filter: blur(16px); border: 1px solid {stepper_border}; border-radius: 16px; padding: 12px 20px; margin-bottom: 20px; display: flex; align-items: center; justify-content: space-between; flex-wrap: wrap; gap: 10px;">
        <div style="display: flex; align-items: center; gap: 8px;">
            <span style="background: {s1_bg}; color: {s1_fg}; padding: 4px 12px; border-radius: 9999px; font-weight: bold; font-size: 0.8rem;">1. Setup</span>
            <span style="color: #94A3B8;">→</span>
            <span style="background: {s2_bg}; color: {s2_fg}; padding: 4px 12px; border-radius: 9999px; font-weight: bold; font-size: 0.8rem;">2. Map & Rooms</span>
            <span style="color: #94A3B8;">→</span>
            <span style="background: {s3_bg}; color: {s3_fg}; padding: 4px 12px; border-radius: 9999px; font-weight: bold; font-size: 0.8rem;">3. Curriculum & Faculty</span>
            <span style="color: #94A3B8;">→</span>
            <span style="background: {s4_bg}; color: {s4_fg}; padding: 4px 12px; border-radius: 9999px; font-weight: bold; font-size: 0.8rem;">4. Timetable & Transit</span>
        </div>
        <div style="font-size: 0.82rem; font-weight: 600;">
            🏢 <b>{nodes_cnt}</b> Buildings | 🏫 <b>{rooms_cnt}</b> Rooms (<b>{cap_total}</b> Seats) | 🎓 <b>{majors_cnt}</b> Majors | 👨‍🏫 <b>{lects_cnt}</b> Lecturers | 📖 <b>{subjs_cnt}</b> Subjects | 🌲 MST: <b>{mst_dist:,.0f}m</b>
        </div>
    </div>
    """
    st.markdown(stepper_html, unsafe_allow_html=True)


def render_version_log():
    file1.apply_custom_css()
    
    st.markdown('<div class="brand-badge">📜 SCHEDPATH Release History</div>', unsafe_allow_html=True)
    st.markdown('<div class="schedpath-title">System Version Log & Release Notes</div>', unsafe_allow_html=True)
    st.markdown('<div class="schedpath-subtitle">Track feature updates, optimization milestones, and constraint satisfaction enhancements.</div>', unsafe_allow_html=True)

    st.markdown('<div class="clean-card">', unsafe_allow_html=True)
    st.markdown("## 🌌 v2.1.0 — Custom Backgrounds & Glassmorphism Theme Suite (Current)")
    st.markdown("""
- **Dynamic Background Theme Switcher**: 4 stunning themes available in sidebar (`🌌 Midnight Glassmorphism`, `🔮 Deep Violet Cyberpunk`, `🌊 Emerald Cyber-Deck`, ` Pearl Silver`).
- **Glassmorphic UI Cards**: Backdrop blur (`backdrop-filter: blur(16px)`), luminous radial mesh gradients, and glowing borders.
- **Cyber-Deck Map Graph**: Matplotlib campus node graph styled with glowing dark themes, high-contrast cyan building badges, and bright red MST edges.
- **Dark Mode Timetables**: Styled HTML timetable grids with glowing status badges (`📚 Lecture`, `🔬 Specialized`, `☕ Break`).
""")
    st.markdown('</div>', unsafe_allow_html=True)

    st.markdown('<div class="clean-card">', unsafe_allow_html=True)
    st.markdown("## 🏷️ v2.0.0 — Custom Room Specs & Faculty Non-Overlap Engine")
    st.markdown("""
- **Custom Room Specs**: Define specialized usages (`Simulation Lab`, `X-Ray Practicum`, `Dental Practice`) across Steps 2 & 3.
- **Faculty Roster**: Register faculty members and assign lecturers to subjects in Step 3.
- **Lecturer Non-Overlap Constraint**: Hard constraint engine ensuring faculty are never double-booked across different subjects or unjoined slots.
- **Faculty Timetables**: Dedicated **👨‍🏫 Schedule by Lecturer** view in Step 4 with personal CSV schedule downloads.
""")
    st.markdown('</div>', unsafe_allow_html=True)

    st.markdown('<div class="clean-card">', unsafe_allow_html=True)
    st.markdown("## 🎨 v1.3.0 — UI/UX Optimization & One-Click Exporters")
    st.markdown("""
- **Pure HTML Fast Tables**: Instant loading times without PyArrow serialization freezes.
- **Workflow Stepper & Dynamic KPI Header**: Top progress indicator and live system metrics.
- **One-Click CSV Exporters**: Instant downloads for Major Timetables, Master Schedules, and Walking Transit Reports.
""")
    st.markdown('</div>', unsafe_allow_html=True)

    st.markdown('<div class="clean-card">', unsafe_allow_html=True)
    st.markdown("## 🏃 v1.2.0 — MST Pathfinding & Daily Walking Distance Engine")
    st.markdown("""
- **Walking Transit Calculation**: Traces NetworkX Dijkstra shortest paths across MST map edges (`calculate_walking_distance_per_day`).
- **Walking Distribution Matrix**: Summary matrix and route breakdown of meters walked per cohort per day.
""")
    st.markdown('</div>', unsafe_allow_html=True)

    if st.button("← Back to Application Workspace", use_container_width=False):
        st.session_state.current_page = "file1"
        st.rerun()


# Page Router
if st.session_state.current_page == "file1":
    file1.render()
elif st.session_state.current_page == "file2":
    file2.render()
elif st.session_state.current_page == "file3":
    file3.render()
elif st.session_state.current_page == "file4":
    file4.render()
elif st.session_state.current_page == "vlog":
    render_version_log()
