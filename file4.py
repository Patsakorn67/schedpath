import streamlit as st
import pandas as pd
import networkx as nx
import file1

DAYS_OF_WEEK = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]
TIME_SLOTS = [f"{h:02d}:00" for h in range(8, 17)] # 08:00 to 16:00 (9 start hours)
SLOT_LABELS = [f"{h:02d}:00 - {h+1:02d}:00" for h in range(8, 17)] # 9 time window labels

def calculate_walking_distance_per_day(data):
    timetable = data.get("timetable", {})
    edges = data.get("edges", [])
    
    G = nx.Graph()
    for e in edges:
        try:
            u, v, dist = e["from"], e["to"], float(e["distance"])
            G.add_edge(u, v, weight=dist)
        except (KeyError, ValueError):
            continue

    daily_distances = {}

    for m_name, slots in timetable.items():
        daily_distances[m_name] = {}
        
        for day in DAYS_OF_WEEK:
            day_slots = [
                s for s in slots 
                if s.get("day") == day and not s.get("is_break") and s.get("building") not in ["Campus-wide", "N/A", ""]
            ]
            
            def parse_start(x):
                try:
                    return int(x["start_time"].split(":")[0])
                except Exception:
                    return 0

            day_slots.sort(key=parse_start)
            
            total_day_dist = 0.0
            transitions = []
            
            for i in range(len(day_slots) - 1):
                prev_slot = day_slots[i]
                curr_slot = day_slots[i+1]
                
                bld_from = prev_slot.get("building")
                bld_to = curr_slot.get("building")
                
                if bld_from and bld_to and bld_from != bld_to:
                    dist = 0.0
                    path = []
                    if G.has_node(bld_from) and G.has_node(bld_to):
                        try:
                            dist = nx.shortest_path_length(G, source=bld_from, target=bld_to, weight="weight")
                            path = nx.shortest_path(G, source=bld_from, target=bld_to, weight="weight")
                        except nx.NetworkXNoPath:
                            dist = 0.0
                    
                    total_day_dist += dist
                    transitions.append({
                        "time": f"{prev_slot['end_time']} → {curr_slot['start_time']}",
                        "from_subject": prev_slot["subject"],
                        "from_building": bld_from,
                        "from_room": prev_slot.get("room", ""),
                        "to_subject": curr_slot["subject"],
                        "to_building": bld_to,
                        "to_room": curr_slot.get("room", ""),
                        "distance_m": dist,
                        "path": " → ".join(path) if path else f"{bld_from} → {bld_to}"
                    })
            
            daily_distances[m_name][day] = {
                "total_distance_m": total_day_dist,
                "transitions": transitions
            }

    return daily_distances


def generate_automated_timetable(data):
    majors = data.get("majors", [])
    subjects = data.get("subjects", [])
    rooms = data.get("rooms", [])
    breaks = data.get("breaks", [])

    if not majors or not subjects or not rooms:
        return {}, "Missing required setup data (Majors, Subjects, or Rooms)."

    timetable = {m["name"]: [] for m in majors}
    
    room_occupancy = set()      # (day, t_slot, room_name)
    major_occupancy = set()     # (day, t_slot, major_name)
    lecturer_occupancy = set()  # (day, t_slot, lecturer_name)

    # 1. Block break slots
    for b in breaks:
        b_name = b["name"]
        b_scope = b.get("scope", "All Majors")
        b_days = b.get("days", [])
        b_start = b.get("start_time", "12:00")
        b_end = b.get("end_time", "13:00")

        start_h = int(b_start.split(":")[0])
        end_h = int(b_end.split(":")[0])

        target_m_list = [m["name"] for m in majors] if b_scope == "All Majors" else [b_scope]

        for day in b_days:
            for h in range(start_h, end_h):
                t_slot = f"{h:02d}:00"
                for m_name in target_m_list:
                    if m_name in timetable:
                        major_occupancy.add((day, t_slot, m_name))
                        timetable[m_name].append({
                            "day": day,
                            "start_time": f"{h:02d}:00",
                            "end_time": f"{h+1:02d}:00",
                            "subject": f"☕ {b_name}",
                            "room": "N/A",
                            "building": "Campus-wide",
                            "is_break": True,
                            "lecturer": "—"
                        })

    major_students = {m["name"]: m["students"] for m in majors}

    def find_best_room_for_headcount(total_headcount, req_usage, day, start_h, duration):
        capacity_suitable = [r for r in rooms if r["capacity"] >= total_headcount]
        if not capacity_suitable:
            return None

        exact_matches = []
        gen_lecture_matches = []

        for r in capacity_suitable:
            r_usage = r.get("usage", "General Lecture")
            if req_usage == "General Lecture":
                if r_usage in ["General Lecture", "Classroom", "Lecture Room"]:
                    exact_matches.append(r)
            else:
                if r_usage == req_usage:
                    exact_matches.append(r)
                elif r_usage in ["General Lecture", "Classroom", "Lecture Room"]:
                    gen_lecture_matches.append(r)

        for candidate_group in [exact_matches, gen_lecture_matches]:
            if not candidate_group:
                continue

            valid_candidates = []
            for r in candidate_group:
                available = True
                for h in range(start_h, start_h + duration):
                    t_slot = f"{h:02d}:00"
                    if (day, t_slot, r["name"]) in room_occupancy:
                        available = False
                        break
                if available:
                    valid_candidates.append(r)

            if valid_candidates:
                valid_candidates.sort(key=lambda x: x["capacity"])
                return valid_candidates[0]

        return None

    # Process each subject
    for s in subjects:
        s_code = s.get("code", "").strip()
        s_name = s["name"]
        s_duration = int(s.get("hours_per_period", 2))
        req_usage = s.get("required_usage", "General Lecture")
        lecturer = s.get("lecturer", "Unassigned")
        target_m_list = [m for m in s.get("majors", [s.get("major", "")]) if m in timetable]

        if not target_m_list:
            continue

        # Strategy A: Try joint session
        combined_headcount = sum(major_students.get(m, 0) for m in target_m_list)
        joint_scheduled = False

        for day in DAYS_OF_WEEK:
            if joint_scheduled:
                break

            for start_h in range(8, 17 - s_duration + 1):
                all_majors_free = True
                for m_name in target_m_list:
                    for h in range(start_h, start_h + s_duration):
                        t_slot = f"{h:02d}:00"
                        if (day, t_slot, m_name) in major_occupancy:
                            all_majors_free = False
                            break
                    if not all_majors_free:
                        break

                if not all_majors_free:
                    continue

                lecturer_free = True
                if lecturer != "Unassigned":
                    for h in range(start_h, start_h + s_duration):
                        t_slot = f"{h:02d}:00"
                        if (day, t_slot, lecturer) in lecturer_occupancy:
                            lecturer_free = False
                            break

                if not lecturer_free:
                    continue

                selected_room = find_best_room_for_headcount(combined_headcount, req_usage, day, start_h, s_duration)
                if selected_room:
                    for h in range(start_h, start_h + s_duration):
                        t_slot = f"{h:02d}:00"
                        room_occupancy.add((day, t_slot, selected_room["name"]))
                        if lecturer != "Unassigned":
                            lecturer_occupancy.add((day, t_slot, lecturer))
                        for m_name in target_m_list:
                            major_occupancy.add((day, t_slot, m_name))

                    for m_name in target_m_list:
                        timetable[m_name].append({
                            "day": day,
                            "start_time": f"{start_h:02d}:00",
                            "end_time": f"{start_h + s_duration:02d}:00",
                            "code": s_code,
                            "subject": s_name,
                            "room": selected_room["name"],
                            "building": selected_room["building"],
                            "is_break": False,
                            "req_usage": req_usage,
                            "lecturer": lecturer
                        })
                    joint_scheduled = True
                    break

        # Strategy B: Individual fallback
        if not joint_scheduled:
            for m_name in target_m_list:
                already = any(slot["subject"] == s_name for slot in timetable[m_name] if not slot.get("is_break"))
                if already:
                    continue

                for day in DAYS_OF_WEEK:
                    m_scheduled = False
                    for start_h in range(8, 17 - s_duration + 1):
                        is_free = True
                        for h in range(start_h, start_h + s_duration):
                            t_slot = f"{h:02d}:00"
                            if (day, t_slot, m_name) in major_occupancy:
                                is_free = False
                                break
                        if not is_free:
                            continue

                        lecturer_free = True
                        if lecturer != "Unassigned":
                            for h in range(start_h, start_h + s_duration):
                                t_slot = f"{h:02d}:00"
                                if (day, t_slot, lecturer) in lecturer_occupancy:
                                    lecturer_free = False
                                    break

                        if not lecturer_free:
                            continue

                        indiv_headcount = major_students.get(m_name, 0)
                        selected_room = find_best_room_for_headcount(indiv_headcount, req_usage, day, start_h, s_duration)
                        if selected_room:
                            for h in range(start_h, start_h + s_duration):
                                t_slot = f"{h:02d}:00"
                                major_occupancy.add((day, t_slot, m_name))
                                room_occupancy.add((day, t_slot, selected_room["name"]))
                                if lecturer != "Unassigned":
                                    lecturer_occupancy.add((day, t_slot, lecturer))

                            timetable[m_name].append({
                                "day": day,
                                "start_time": f"{start_h:02d}:00",
                                "end_time": f"{start_h + s_duration:02d}:00",
                                "code": s_code,
                                "subject": s_name,
                                "room": selected_room["name"],
                                "building": selected_room["building"],
                                "is_break": False,
                                "req_usage": req_usage,
                                "lecturer": lecturer
                            })
                            m_scheduled = True
                            break
                    if m_scheduled:
                        break

    return timetable, "Successfully generated automated schedule output with lecturer & room spec constraints!"


def render():
    file1.apply_custom_css()
    theme = st.session_state.get("app_theme", "🌌 Midnight Glassmorphism")
    is_light = (theme == " Pearl Silver")
    
    if "save_data" not in st.session_state or not st.session_state.save_data:
        st.warning("⚠️ No active save file found. Please load or create a save file in Step 1.")
        if st.button("Go to Step 1"):
            st.session_state.current_page = "file1"
            st.rerun()
        return

    data = st.session_state.save_data
    save_name = st.session_state.active_save

    st.markdown(f'<div class="brand-badge">📅 Step 4 Workspace | Save: {save_name}</div>', unsafe_allow_html=True)
    st.markdown('<div class="schedpath-title" style="font-size: 2.3rem;">Automated Timetable Output</div>', unsafe_allow_html=True)
    st.markdown('<div class="schedpath-subtitle">Generate constraint-based weekly timetables, enforce non-overlapping lecturer schedules, calculate walking distances, and export master schedules.</div>', unsafe_allow_html=True)

    # Control Panel Card
    st.markdown('<div class="clean-card">', unsafe_allow_html=True)
    st.subheader("⚙️ Schedule Generation Engine")
    
    gen_col1, gen_col2 = st.columns([2, 1])
    with gen_col1:
        st.write("Click below to run joint-major capacity matching, lecturer non-overlap constraints, and room spec scheduling.")
    with gen_col2:
        if st.button("🚀 Generate Automated Timetable", use_container_width=True):
            timetable_output, msg = generate_automated_timetable(data)
            data["timetable"] = timetable_output
            file1.save_data_to_file(save_name, data)
            st.toast("Generated automated timetable output!", icon="🚀")
            st.success(msg)
            st.rerun()

    if data.get("timetable"):
        if st.button("🗑️ Clear Timetable", type="secondary"):
            data["timetable"] = {}
            file1.save_data_to_file(save_name, data)
            st.toast("Cleared active timetable.", icon="🗑️")
            st.warning("Cleared timetable output.")
            st.rerun()
            
    st.markdown('</div>', unsafe_allow_html=True)

    timetable = data.get("timetable", {})
    
    # Table Styling Variables
    hdr_bg = "#0F172A" if not is_light else "#0F172A"
    hdr_fg = "#38BDF8" if not is_light else "#FFFFFF"
    cell_border = "1px solid rgba(255,255,255,0.1)" if not is_light else "1px solid #CBD5E1"
    day_bg = "#1E293B" if not is_light else "#F1F5F9"
    day_fg = "#F8FAFC" if not is_light else "#0F172A"
    empty_bg = "rgba(15, 23, 42, 0.5)" if not is_light else "#FFFFFF"
    text_sub = "#475569" if is_light else "#94A3B8"
    
    if timetable:
        tab_majors, tab_lecturers, tab_rooms, tab_distances, tab_master = st.tabs([
            "🎓 Schedule by Major", 
            "👨‍🏫 Schedule by Lecturer",
            "🏫 Schedule by Room", 
            "🏃 Building Walking Distances", 
            "📋 Master Schedule Table"
        ])

        # Global Search Filter
        search_query = st.text_input("🔍 Search / Filter Schedule by Keyword (e.g. English, Dr. Somchai, Room 101, RT):", key="global_schedule_search").strip().lower()

        # --- TAB 1: SCHEDULE BY MAJOR ---
        with tab_majors:
            st.markdown('<div class="clean-card">', unsafe_allow_html=True)
            major_names = list(timetable.keys())
            
            if major_names:
                m_hdr_col1, m_hdr_col2 = st.columns([2, 1])
                with m_hdr_col1:
                    sel_m = st.selectbox("Select Major View:", major_names, key="view_sel_major")
                
                m_slots = timetable[sel_m]
                grid = {d: {t: "-" for t in TIME_SLOTS} for d in DAYS_OF_WEEK}

                for slot in m_slots:
                    d = slot["day"]
                    s_h = int(slot["start_time"].split(":")[0])
                    e_h = int(slot["end_time"].split(":")[0])
                    
                    cell_text = slot["subject"]
                    building = slot.get("building", "")
                    room = slot.get("room", "")
                    lecturer = slot.get("lecturer", "Unassigned")
                    is_break = slot.get("is_break", False)
                    req_usage = slot.get("req_usage", "General Lecture")

                    if search_query and search_query not in cell_text.lower() and search_query not in building.lower() and search_query not in room.lower() and search_query not in lecturer.lower():
                        continue

                    for h in range(s_h, e_h):
                        t_key = f"{h:02d}:00"
                        if t_key in grid[d]:
                            if is_break:
                                grid[d][t_key] = f"☕ <b>{cell_text}</b>"
                            else:
                                if req_usage == "General Lecture":
                                    badge_html = '<span style="background-color: #DCFCE7; color: #15803D; padding: 2px 8px; border-radius: 9999px; font-size: 0.7rem; font-weight: bold;">📚 Lecture</span>'
                                else:
                                    badge_html = f'<span style="background-color: #F3E8FF; color: #6B21A8; padding: 2px 8px; border-radius: 9999px; font-size: 0.7rem; font-weight: bold;">🔬 {req_usage}</span>'
                                
                                lect_html = f"<br><small style='color: {'#38BDF8' if not is_light else '#0284C7'};'>👨‍🏫 {lecturer}</small>" if lecturer != "Unassigned" else ""
                                grid[d][t_key] = f"{badge_html}<br><b>{cell_text}</b><br><small>📍 {building} ({room})</small>{lect_html}"

                df_grid = pd.DataFrame(grid).T
                df_grid.columns = SLOT_LABELS
                
                html_table = "<div style='overflow-x: auto;'><table style='width:100%; border-collapse: collapse; font-family: sans-serif; text-align: center; font-size: 0.88rem;'>"
                html_table += f"<tr style='background-color: {hdr_bg}; color: {hdr_fg};'><th style='padding: 10px; border: {cell_border};'>Day / Time</th>"
                for col in df_grid.columns:
                    html_table += f"<th style='padding: 10px; border: {cell_border};'>{col}</th>"
                html_table += "</tr>"

                for day in DAYS_OF_WEEK:
                    html_table += f"<tr><td style='font-weight: bold; background-color: {day_bg}; color: {day_fg}; padding: 10px; border: {cell_border};'>{day}</td>"
                    for col in df_grid.columns:
                        cell_val = df_grid.loc[day, col]
                        bg_color = empty_bg
                        if "☕" in cell_val:
                            bg_color = "#FEF3C7" if is_light else "rgba(180, 83, 9, 0.28)"
                        elif "📚" in cell_val:
                            bg_color = "#F0FDF4" if is_light else "rgba(22, 101, 52, 0.28)"
                        elif "🔬" in cell_val:
                            bg_color = "#FAF5FF" if is_light else "rgba(107, 33, 168, 0.28)"
                        html_table += f"<td style='padding: 8px; border: {cell_border}; background-color: {bg_color};'>{cell_val}</td>"
                    html_table += "</tr>"
                html_table += "</table></div>"

                st.markdown(html_table, unsafe_allow_html=True)

                st.write("")
                df_export = pd.DataFrame(m_slots)
                csv_major = df_export.to_csv(index=False).encode('utf-8')
                st.download_button(
                    label=f"📥 Download {sel_m} Timetable CSV",
                    data=csv_major,
                    file_name=f"{sel_m.replace(' ', '_')}_timetable.csv",
                    mime="text/csv"
                )
            else:
                st.info("No major timetables generated.")
            st.markdown('</div>', unsafe_allow_html=True)

        # --- TAB 2: SCHEDULE BY LECTURER ---
        with tab_lecturers:
            st.markdown('<div class="clean-card">', unsafe_allow_html=True)
            all_lecturers = [l["name"] for l in data.get("lecturers", [])]

            if all_lecturers:
                sel_l = st.selectbox("Select Faculty Lecturer View:", all_lecturers, key="view_sel_lecturer")
                st.subheader(f"👨‍🏫 Weekly Teaching Schedule: {sel_l}")

                l_grid = {d: {t: "-" for t in TIME_SLOTS} for d in DAYS_OF_WEEK}

                for m_name, m_slots in timetable.items():
                    for slot in m_slots:
                        if slot.get("lecturer") == sel_l:
                            d = slot["day"]
                            s_h = int(slot["start_time"].split(":")[0])
                            e_h = int(slot["end_time"].split(":")[0])
                            subj = slot["subject"]
                            building = slot.get("building", "")
                            room = slot.get("room", "")

                            if search_query and search_query not in subj.lower() and search_query not in m_name.lower() and search_query not in building.lower():
                                continue

                            for h in range(s_h, e_h):
                                t_key = f"{h:02d}:00"
                                if t_key in l_grid[d]:
                                    existing_txt = l_grid[d][t_key]
                                    if existing_txt == "-":
                                        l_grid[d][t_key] = f"<b>{subj}</b><br><small>🎓 {m_name}<br>📍 {building} ({room})</small>"
                                    elif m_name not in existing_txt:
                                        l_grid[d][t_key] += f", {m_name}"

                df_lgrid = pd.DataFrame(l_grid).T
                df_lgrid.columns = SLOT_LABELS

                html_ltable = "<div style='overflow-x: auto;'><table style='width:100%; border-collapse: collapse; font-family: sans-serif; text-align: center; font-size: 0.88rem;'>"
                html_ltable += f"<tr style='background-color: {hdr_bg}; color: {hdr_fg};'><th style='padding: 10px; border: {cell_border};'>Day / Time</th>"
                for col in df_lgrid.columns:
                    html_ltable += f"<th style='padding: 10px; border: {cell_border};'>{col}</th>"
                html_ltable += "</tr>"

                for day in DAYS_OF_WEEK:
                    html_ltable += f"<tr><td style='font-weight: bold; background-color: {day_bg}; color: {day_fg}; padding: 10px; border: {cell_border};'>{day}</td>"
                    for col in df_lgrid.columns:
                        cell_val = df_lgrid.loc[day, col]
                        bg_color = empty_bg if cell_val == "-" else ("#EFF6FF" if is_light else "rgba(30, 58, 138, 0.35)")
                        html_ltable += f"<td style='padding: 8px; border: {cell_border}; background-color: {bg_color};'>{cell_val}</td>"
                    html_ltable += "</tr>"
                html_ltable += "</table></div>"

                st.markdown(html_ltable, unsafe_allow_html=True)
            else:
                st.info("No faculty lecturers registered yet. Add lecturers in Step 3 (Curriculum & Faculty).")
            st.markdown('</div>', unsafe_allow_html=True)

        # --- TAB 3: SCHEDULE BY ROOM ---
        with tab_rooms:
            st.markdown('<div class="clean-card">', unsafe_allow_html=True)
            all_rooms = [r["name"] for r in data.get("rooms", [])]

            if all_rooms:
                sel_r = st.selectbox("Select Room View:", all_rooms, key="view_sel_room")
                st.subheader(f"🏫 Weekly Room Occupancy: {sel_r}")

                r_grid = {d: {t: "-" for t in TIME_SLOTS} for d in DAYS_OF_WEEK}

                for m_name, m_slots in timetable.items():
                    for slot in m_slots:
                        if slot.get("room") == sel_r:
                            d = slot["day"]
                            s_h = int(slot["start_time"].split(":")[0])
                            e_h = int(slot["end_time"].split(":")[0])
                            subj = slot["subject"]
                            lecturer = slot.get("lecturer", "Unassigned")
                            
                            if search_query and search_query not in subj.lower() and search_query not in m_name.lower() and search_query not in lecturer.lower():
                                continue

                            for h in range(s_h, e_h):
                                t_key = f"{h:02d}:00"
                                if t_key in r_grid[d]:
                                    existing_txt = r_grid[d][t_key]
                                    if existing_txt == "-":
                                        r_grid[d][t_key] = f"<b>{subj}</b><br><small>🎓 {m_name}<br>👨‍🏫 {lecturer}</small>"
                                    elif m_name not in existing_txt:
                                        r_grid[d][t_key] += f", {m_name}"

                df_rgrid = pd.DataFrame(r_grid).T
                df_rgrid.columns = SLOT_LABELS

                html_rtable = "<div style='overflow-x: auto;'><table style='width:100%; border-collapse: collapse; font-family: sans-serif; text-align: center; font-size: 0.88rem;'>"
                html_rtable += f"<tr style='background-color: {hdr_bg}; color: {hdr_fg};'><th style='padding: 10px; border: {cell_border};'>Day / Time</th>"
                for col in df_rgrid.columns:
                    html_rtable += f"<th style='padding: 10px; border: {cell_border};'>{col}</th>"
                html_rtable += "</tr>"

                for day in DAYS_OF_WEEK:
                    html_rtable += f"<tr><td style='font-weight: bold; background-color: {day_bg}; color: {day_fg}; padding: 10px; border: {cell_border};'>{day}</td>"
                    for col in df_rgrid.columns:
                        cell_val = df_rgrid.loc[day, col]
                        bg_color = empty_bg if cell_val == "-" else ("#EFF6FF" if is_light else "rgba(30, 58, 138, 0.35)")
                        html_rtable += f"<td style='padding: 8px; border: {cell_border}; background-color: {bg_color};'>{cell_val}</td>"
                    html_rtable += "</tr>"
                html_rtable += "</table></div>"

                st.markdown(html_rtable, unsafe_allow_html=True)
            else:
                st.info("No rooms configured.")
            st.markdown('</div>', unsafe_allow_html=True)

        # --- TAB 4: BUILDING WALKING DISTANCES ---
        with tab_distances:
            st.markdown('<div class="clean-card">', unsafe_allow_html=True)
            st.subheader("🏃 Daily Building Transition & Walking Distance Analysis")
            st.write("Calculates total meters walked by students when switching between different campus buildings across their daily class schedule.")

            walk_data = calculate_walking_distance_per_day(data)
            
            grand_total_m = sum(
                sum(day_info["total_distance_m"] for day_info in m_days.values())
                for m_days in walk_data.values()
            )
            
            m_col1, m_col2 = st.columns(2)
            with m_col1:
                st.metric("Total Campus Weekly Walking Transit", f"{grand_total_m:,.0f} meters")
            with m_col2:
                num_majors = len(walk_data) if walk_data else 1
                st.metric("Avg Walking Transit / Major", f"{(grand_total_m / num_majors):,.0f} meters / week")

            st.write("---")

            # Daily Walking Distance Matrix Table
            st.markdown("### 📊 Weekly Walking Distance Distribution (Meters / Day)")
            
            matrix_html = "<div style='overflow-x: auto;'><table style='width:100%; border-collapse: collapse; font-family: sans-serif; text-align: center; font-size: 0.9rem;'>"
            matrix_html += f"<tr style='background-color: {hdr_bg}; color: {hdr_fg};'><th style='padding: 10px; border: {cell_border};'>Major Cohort</th>"
            for d in DAYS_OF_WEEK:
                matrix_html += f"<th style='padding: 10px; border: {cell_border};'>{d}</th>"
            matrix_html += f"<th style='padding: 10px; border: {cell_border};'>Weekly Total (m)</th></tr>"

            transit_export_rows = []

            for m_name, m_days in walk_data.items():
                m_total = sum(m_days[d]["total_distance_m"] for d in DAYS_OF_WEEK)
                matrix_html += f"<tr><td style='font-weight: bold; background-color: {day_bg}; color: {day_fg}; padding: 10px; border: {cell_border};'>{m_name}</td>"
                
                row_dict = {"Major": m_name, "Weekly Total (m)": m_total}
                
                for d in DAYS_OF_WEEK:
                    d_m = m_days[d]["total_distance_m"]
                    row_dict[d] = d_m
                    badge_style = f"color: {text_sub};" if d_m == 0 else "color: #38BDF8; font-weight: bold;"
                    matrix_html += f"<td style='padding: 8px; border: {cell_border}; {badge_style}'>{d_m:,.0f} m</td>"
                
                matrix_html += f"<td style='font-weight: bold; background-color: rgba(220, 38, 38, 0.2); color: #FCA5A5; padding: 10px; border: {cell_border};'>{m_total:,.0f} m</td></tr>"
                transit_export_rows.append(row_dict)
                
            matrix_html += "</table></div>"
            st.markdown(matrix_html, unsafe_allow_html=True)

            st.write("")
            df_transit_export = pd.DataFrame(transit_export_rows)
            csv_transit = df_transit_export.to_csv(index=False).encode('utf-8')
            st.download_button(
                label="📥 Download Walking Transit Report CSV",
                data=csv_transit,
                file_name="walking_transit_report.csv",
                mime="text/csv"
            )

            st.write("---")
            
            maj_options = list(walk_data.keys())
            if maj_options:
                sel_m_dist = st.selectbox("Select Major for Detailed Transitions:", maj_options, key="sel_m_dist")
                
                m_days = walk_data[sel_m_dist]
                total_m_for_major = sum(d["total_distance_m"] for d in m_days.values())
                
                st.markdown(f"#### 🎓 Transit Route Details: **{sel_m_dist}** (Weekly Total: `{total_m_for_major:,.0f} m`) font-weight: bold;")
                
                t_html = "<div style='overflow-x: auto;'><table style='width:100%; border-collapse: collapse; font-family: sans-serif; text-align: left; font-size: 0.88rem;'>"
                t_html += f"<tr style='background-color: {hdr_bg}; color: {hdr_fg};'><th style='padding: 10px; border: {cell_border};'>Day</th><th style='padding: 10px; border: {cell_border};'>Time Window</th><th style='padding: 10px; border: {cell_border};'>From Class</th><th style='padding: 10px; border: {cell_border};'>To Class</th><th style='padding: 10px; border: {cell_border};'>MST Route Path</th><th style='padding: 10px; border: {cell_border};'>Distance</th></tr>"

                for day in DAYS_OF_WEEK:
                    d_info = m_days.get(day, {"total_distance_m": 0, "transitions": []})
                    transitions = d_info["transitions"]
                    
                    if not transitions:
                        t_html += f"<tr><td style='font-weight: bold; background-color: {day_bg}; color: {day_fg}; padding: 10px; border: {cell_border};'>{day}</td><td colspan='5' style='padding: 10px; border: {cell_border}; opacity: 0.6;'>No building changes required</td></tr>"
                    else:
                        for idx, tr in enumerate(transitions):
                            day_label = day if idx == 0 else ""
                            t_html += f"<tr><td style='font-weight: bold; background-color: {day_bg}; color: {day_fg}; padding: 10px; border: {cell_border};'>{day_label}</td>"
                            t_html += f"<td style='padding: 8px; border: {cell_border};'>{tr['time']}</td>"
                            t_html += f"<td style='padding: 8px; border: {cell_border};'><b>{tr['from_subject']}</b><br><small>{tr['from_building']} ({tr['from_room']})</small></td>"
                            t_html += f"<td style='padding: 8px; border: {cell_border};'><b>{tr['to_subject']}</b><br><small>{tr['to_building']} ({tr['to_room']})</small></td>"
                            t_html += f"<td style='padding: 8px; border: {cell_border};'><code>{tr['path']}</code></td>"
                            t_html += f"<td style='padding: 8px; border: {cell_border}; font-weight: bold; color: #38BDF8;'>{tr['distance_m']:,.0f} m</td></tr>"

                t_html += "</table></div>"
                st.markdown(t_html, unsafe_allow_html=True)

            else:
                st.info("No major distance records found.")

            st.markdown('</div>', unsafe_allow_html=True)

        # --- TAB 5: MASTER SCHEDULE TABLE ---
        with tab_master:
            st.markdown('<div class="clean-card">', unsafe_allow_html=True)
            st.subheader("📋 Master Class & Activity Schedule")

            master_rows = []
            for m_name, m_slots in timetable.items():
                for slot in m_slots:
                    subj = slot["subject"]
                    bld = slot["building"]
                    rm = slot["room"]
                    lect = slot.get("lecturer", "Unassigned")
                    
                    if search_query and search_query not in subj.lower() and search_query not in m_name.lower() and search_query not in bld.lower() and search_query not in rm.lower() and search_query not in lect.lower():
                        continue

                    master_rows.append({
                        "Major": m_name,
                        "Day": slot["day"],
                        "Time Window": f"{slot['start_time']} - {slot['end_time']}",
                        "Subject / Activity": subj,
                        "Assigned Lecturer": lect,
                        "Building Location": bld,
                        "Room": rm
                    })

            if master_rows:
                df_master = pd.DataFrame(master_rows)
                st.dataframe(df_master, use_container_width=True)

                st.write("")
                csv_master = df_master.to_csv(index=False).encode('utf-8')
                st.download_button(
                    label="📥 Download Master Schedule CSV",
                    data=csv_master,
                    file_name="master_schedule.csv",
                    mime="text/csv"
                )
            else:
                st.info("No schedule entries match search query.")
            st.markdown('</div>', unsafe_allow_html=True)

    else:
        st.info("💡 Click **'🚀 Generate Automated Timetable'** above to calculate and build your schedule output.")

    # Bottom Navigation Button
    st.write("")
    if st.button("← Back to Step 3 (Curriculum & Faculty)", type="secondary"):
        st.session_state.current_page = "file3"
        st.rerun()
