import uuid
import streamlit as st
import file1

DAYS_OF_WEEK = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]
TIME_SLOTS = [f"{h:02d}:00" for h in range(8, 18)] # 08:00 to 17:00

DEFAULT_ROOM_SPECS = [
    "For Anatomy Class",
    "General Lecture",
    "Laboratory",
    "Radiological Technology School",
    "Human Kinetics and Health School",
    "Paramedic School"
]

EDIT_PREFIXES = ("edit_name_", "edit_code_", "edit_majors_", "edit_hours_", "edit_room_", "edit_lecturer_")

def get_all_specs(data):
    custom = data.get("custom_specs", [])
    specs = list(DEFAULT_ROOM_SPECS)
    for c in custom:
        if c not in specs:
            specs.append(c)
    return specs

def ensure_subject_fields(data):
    changed = False
    data.setdefault("lecturers", [])
    for s in data["subjects"]:
        if "id" not in s:
            s["id"] = uuid.uuid4().hex[:8]
            changed = True
        if "code" not in s:
            s["code"] = ""
            changed = True
        if "lecturer" not in s:
            s["lecturer"] = "Unassigned"
            changed = True
    return changed

def find_subject(data, sid):
    for s in data["subjects"]:
        if s.get("id") == sid:
            return s
    return None

def clear_edit_state(sid):
    for prefix in EDIT_PREFIXES:
        st.session_state.pop(prefix + sid, None)

def subject_label(s):
    code = s.get("code", "").strip()
    lect = s.get("lecturer", "Unassigned")
    return f"{code} - {s['name']} (Lecturer: {lect})" if code else f"{s['name']} (Lecturer: {lect})"

def add_subject(save_name):
    data = st.session_state.save_data
    all_specs = get_all_specs(data)
    majors = st.session_state.get("select_subj_majors", [])
    code = st.session_state.get("input_subj_code", "").strip()
    name = st.session_state.get("input_subj_name", "").strip()
    hours = int(st.session_state.get("input_study_hours", 2))
    room = st.session_state.get("select_room_spec", all_specs[0] if all_specs else "General Lecture")
    lecturer = st.session_state.get("select_subj_lecturer", "Unassigned")

    if not majors:
        st.session_state.subj_msg = ("error", "Please select at least one Major first!")
        return
    if not code:
        st.session_state.subj_msg = ("error", "Please enter a subject code.")
        return
    if not name:
        st.session_state.subj_msg = ("error", "Please enter a valid subject name.")
        return

    for s in data["subjects"]:
        if s.get("code", "").strip().lower() == code.lower() and s["name"].strip().lower() != name.lower():
            st.session_state.subj_msg = ("error", f"Code '{code}' is already used by '{s['name']}'.")
            return

    existing = next((s for s in data["subjects"] if s["name"].strip().lower() == name.lower()), None)

    if existing:
        curr = set(existing.get("majors", [existing.get("major", "")]))
        existing["majors"] = sorted(curr.union(majors))
        existing.pop("major", None)
        existing["code"] = code
        existing["hours_per_period"] = hours
        existing["required_usage"] = room
        existing["lecturer"] = lecturer
        clear_edit_state(existing["id"])
        msg = f"Updated subject '{name}' ({code}) for: {', '.join(majors)}."
    else:
        data["subjects"].append({
            "id": uuid.uuid4().hex[:8],
            "name": name,
            "code": code,
            "majors": list(majors),
            "hours_per_period": hours,
            "required_usage": room,
            "lecturer": lecturer
        })
        msg = f"Added subject '{name}' ({code}) for: {', '.join(majors)}."

    file1.save_data_to_file(save_name, data)
    st.session_state.subj_msg = ("success", msg)

    st.session_state["select_subj_majors"] = []
    st.session_state["input_subj_code"] = ""
    st.session_state["input_subj_name"] = ""


def save_subject_edit(save_name, sid):
    data = st.session_state.save_data
    subj = find_subject(data, sid)
    if subj is None:
        st.session_state.edit_msg = ("error", "Subject no longer exists.")
        return

    new_name = st.session_state.get(f"edit_name_{sid}", "").strip()
    new_code = st.session_state.get(f"edit_code_{sid}", "").strip()
    new_majors = list(st.session_state.get(f"edit_majors_{sid}", []))
    new_hours = int(st.session_state.get(f"edit_hours_{sid}", subj["hours_per_period"]))
    new_room = st.session_state.get(f"edit_room_{sid}", subj.get("required_usage", DEFAULT_ROOM_SPECS[0]))
    new_lect = st.session_state.get(f"edit_lecturer_{sid}", subj.get("lecturer", "Unassigned"))

    if not new_name:
        st.session_state.edit_msg = ("error", "Subject name can't be empty.")
        return
    if not new_code:
        st.session_state.edit_msg = ("error", "Subject code can't be empty.")
        return
    if not new_majors:
        st.session_state.edit_msg = ("error", "A subject needs at least one major.")
        return

    for other in data["subjects"]:
        if other["id"] == sid:
            continue
        if other["name"].strip().lower() == new_name.lower():
            st.session_state.edit_msg = ("error", f"Another subject is already named '{new_name}'.")
            return
        if other.get("code", "").strip().lower() == new_code.lower():
            st.session_state.edit_msg = ("error", f"Code '{new_code}' is already used by '{other['name']}'.")
            return

    subj["name"] = new_name
    subj["code"] = new_code
    subj["majors"] = new_majors
    subj.pop("major", None)
    subj["hours_per_period"] = new_hours
    subj["required_usage"] = new_room
    subj["lecturer"] = new_lect

    clear_edit_state(sid)
    file1.save_data_to_file(save_name, data)
    st.session_state.edit_msg = ("success", f"Saved changes to subject '{new_name}'.")


def delete_subject(save_name, sid):
    data = st.session_state.save_data
    subj = find_subject(data, sid)
    name = subj["name"] if subj else "Subject"
    data["subjects"] = [s for s in data["subjects"] if s["id"] != sid]
    clear_edit_state(sid)
    st.session_state.pop("edit_subj_select", None)
    file1.save_data_to_file(save_name, data)
    st.session_state.edit_msg = ("warning", f"Deleted subject '{name}'.")


def render():
    file1.apply_custom_css()

    if "save_data" not in st.session_state or not st.session_state.save_data:
        st.warning("⚠️ No active save file found. Please load or create a save file in Step 1.")
        if st.button("Go to Step 1"):
            st.session_state.current_page = "file1"
            st.rerun()
        return

    data = st.session_state.save_data
    save_name = st.session_state.active_save

    data.setdefault("majors", [])
    data.setdefault("subjects", [])
    data.setdefault("breaks", [])
    data.setdefault("custom_specs", [])
    data.setdefault("lecturers", [])

    if ensure_subject_fields(data):
        file1.save_data_to_file(save_name, data)

    all_specs = get_all_specs(data)

    st.markdown(f'<div class="brand-badge">🎓 Step 3 Workspace | Save: {save_name}</div>', unsafe_allow_html=True)
    st.markdown('<div class="schedpath-title" style="font-size: 2.3rem;">Curriculum & Faculty Setup</div>', unsafe_allow_html=True)
    st.markdown('<div class="schedpath-subtitle">Register academic majors, faculty lecturers, assign curriculum subjects, and configure recurring break slots.</div>', unsafe_allow_html=True)

    tab_majors, tab_lects, tab_breaks = st.tabs([
        "🎓 5. Majors & Subjects", 
        "👨‍🏫 6. Lecturer Roster", 
        "☕ 7. Breaks & Recurring Activities"
    ])

    # TAB 1: MAJORS & SUBJECTS
    with tab_majors:
        st.markdown('<div class="clean-card">', unsafe_allow_html=True)
        st.subheader("🏷️ Custom Room Specifications")
        st.write("Add custom room usage specs beyond defaults (e.g. 'Simulation Lab', 'X-Ray Room').")

        spec_col1, spec_col2 = st.columns([2, 1])
        with spec_col1:
            new_custom_spec = st.text_input("New Custom Spec Name:", placeholder="e.g. Simulation Laboratory", key="input_new_custom_spec_f3")
        with spec_col2:
            st.write("")
            st.write("")
            if st.button("➕ Add Custom Spec", key="btn_add_cspec_f3", use_container_width=True):
                spec_str = new_custom_spec.strip()
                if not spec_str:
                    st.error("Please enter a valid spec name.")
                elif spec_str.lower() in [s.lower() for s in all_specs]:
                    st.error(f"Specification '{spec_str}' already exists!")
                else:
                    data["custom_specs"].append(spec_str)
                    file1.save_data_to_file(save_name, data)
                    st.toast(f"Added custom spec '{spec_str}'", icon="🏷️")
                    st.success(f"Added custom specification '{spec_str}'.")
                    st.rerun()

        custom_specs = data.get("custom_specs", [])
        if custom_specs:
            st.write("**Your Custom Specifications:**")
            for idx, cs in enumerate(custom_specs):
                cs_col1, cs_col2 = st.columns([3, 1])
                with cs_col1:
                    st.write(f"• 🏷️ **{cs}**")
                with cs_col2:
                    if st.button("Remove", key=f"del_cspec_f3_{idx}", type="secondary", use_container_width=True):
                        data["custom_specs"].pop(idx)
                        file1.save_data_to_file(save_name, data)
                        st.rerun()

        st.markdown('</div>', unsafe_allow_html=True)

        col_major, col_subject = st.columns([1, 1.2])

        # Major Configuration
        with col_major:
            st.markdown('<div class="clean-card">', unsafe_allow_html=True)
            st.subheader("🎓 Academic Majors")

            m_col1, m_col2 = st.columns([1.5, 1])
            with m_col1:
                new_major_name = st.text_input("Major Name:", placeholder="e.g. Medicine", key="input_major_name")
            with m_col2:
                new_major_students = st.number_input("Student Count:", min_value=1, value=40, step=5, key="input_major_students")

            if st.button("➕ Add Major", use_container_width=True):
                if not new_major_name.strip():
                    st.error("Please enter a valid major name.")
                elif any(m["name"] == new_major_name.strip() for m in data["majors"]):
                    st.error(f"Major '{new_major_name.strip()}' already exists!")
                else:
                    data["majors"].append({
                        "name": new_major_name.strip(),
                        "students": int(new_major_students)
                    })
                    file1.save_data_to_file(save_name, data)
                    st.toast(f"Added major '{new_major_name.strip()}' ({new_major_students} students)", icon="🎓")
                    st.success(f"Added Major '{new_major_name.strip()}' ({new_major_students} students).")
                    st.rerun()

            st.write("---")

            if data["majors"]:
                st.write("**Registered Majors:**")
                major_table = []
                for m in data["majors"]:
                    subj_count = 0
                    for s in data["subjects"]:
                        m_list = s.get("majors", [s.get("major", "")])
                        if m["name"] in m_list:
                            subj_count += 1

                    major_table.append({
                        "Major Name": m["name"],
                        "Students": f"{m['students']} students",
                        "Subjects": f"{subj_count} subjects"
                    })
                st.table(major_table)

                major_options = [m["name"] for m in data["majors"]]
                major_to_del = st.selectbox("Select Major to Remove:", major_options, key="del_major_select")
                if st.button("🗑️ Delete Major", type="secondary", use_container_width=True):
                    data["majors"] = [m for m in data["majors"] if m["name"] != major_to_del]
                    updated_subjects = []
                    for s in data["subjects"]:
                        m_list = s.get("majors", [s.get("major", "")])
                        new_m_list = [m for m in m_list if m != major_to_del]
                        if new_m_list:
                            s["majors"] = new_m_list
                            if "major" in s:
                                del s["major"]
                            updated_subjects.append(s)
                        clear_edit_state(s["id"])
                    data["subjects"] = updated_subjects
                    file1.save_data_to_file(save_name, data)
                    st.toast(f"Deleted major '{major_to_del}'", icon="🗑️")
                    st.warning(f"Deleted major '{major_to_del}'.")
                    st.rerun()
            else:
                st.info("No majors registered yet. Add your first academic major above.")

            st.markdown('</div>', unsafe_allow_html=True)

        # Subject Registration
        with col_subject:
            st.markdown('<div class="clean-card">', unsafe_allow_html=True)
            st.subheader("📖 Subject Registration")

            if data["majors"]:
                major_names = [m["name"] for m in data["majors"]]
                lecturer_names = ["Unassigned"] + [l["name"] for l in data.get("lecturers", [])]

                if "select_subj_majors" in st.session_state:
                    st.session_state["select_subj_majors"] = [
                        m for m in st.session_state["select_subj_majors"] if m in major_names
                    ]

                st.multiselect(
                    "Select Major(s) to Study:",
                    options=major_names,
                    key="select_subj_majors"
                )

                c_col1, c_col2 = st.columns([1, 2])
                with c_col1:
                    st.text_input("Subject Code:", placeholder="e.g. MED101", key="input_subj_code")
                with c_col2:
                    st.text_input("Subject Name:", placeholder="e.g. Gross Anatomy I", key="input_subj_name")

                s_col3, s_col4, s_col5 = st.columns([1, 1, 1.2])
                with s_col3:
                    st.number_input("Study Time (Hours/Period):", min_value=1, max_value=4, value=2, step=1, key="input_study_hours")
                with s_col4:
                    st.selectbox("Required Room Spec:", all_specs, key="select_room_spec")
                with s_col5:
                    st.selectbox("Assigned Lecturer:", lecturer_names, key="select_subj_lecturer")

                if st.button("➕ Add Subject", use_container_width=True, on_click=add_subject, args=(save_name,)):
                    pass

                msg = st.session_state.pop("subj_msg", None)
                if msg:
                    if msg[0] == "success":
                        st.toast(msg[1], icon="📖")
                    getattr(st, msg[0])(msg[1])
            else:
                st.info("Please add at least one Academic Major on the left before adding subjects.")

            st.markdown('</div>', unsafe_allow_html=True)

        # Subject Customization Table
        st.markdown('<div class="clean-card">', unsafe_allow_html=True)
        st.subheader("🛠️ Subject Customization")

        if data["subjects"]:
            subj_table = []
            for s in data["subjects"]:
                m_list = s.get("majors", [s.get("major", "")])
                subj_table.append({
                    "Code": s.get("code", "").strip() or "—",
                    "Subject Name": s["name"],
                    "Target Major(s)": ", ".join(m_list),
                    "Duration": f"{s['hours_per_period']} hrs/period",
                    "Room Requirement": s["required_usage"],
                    "Assigned Lecturer": s.get("lecturer", "Unassigned")
                })
            st.table(subj_table)

            st.write("**Edit a subject:** pick one, change anything you need, then press Save.")

            subj_ids = [s["id"] for s in data["subjects"]]
            label_map = {s["id"]: subject_label(s) for s in data["subjects"]}

            if st.session_state.get("edit_subj_select") not in subj_ids:
                st.session_state.pop("edit_subj_select", None)

            sid = st.selectbox(
                "Subject to edit:",
                subj_ids,
                format_func=lambda i: label_map.get(i, i),
                key="edit_subj_select"
            )
            subj = find_subject(data, sid)

            if subj:
                major_names = [m["name"] for m in data["majors"]]
                lecturer_names = ["Unassigned"] + [l["name"] for l in data.get("lecturers", [])]

                saved_majors = [m for m in subj.get("majors", [subj.get("major", "")]) if m in major_names]
                saved_lect = subj.get("lecturer", "Unassigned")
                if saved_lect not in lecturer_names:
                    saved_lect = "Unassigned"

                st.session_state.setdefault(f"edit_name_{sid}", subj["name"])
                st.session_state.setdefault(f"edit_code_{sid}", subj.get("code", ""))
                st.session_state.setdefault(f"edit_majors_{sid}", saved_majors)
                st.session_state.setdefault(f"edit_hours_{sid}", min(max(int(subj["hours_per_period"]), 1), 4))
                st.session_state.setdefault(
                    f"edit_room_{sid}",
                    subj["required_usage"] if subj["required_usage"] in all_specs else (all_specs[0] if all_specs else "General Lecture")
                )
                st.session_state.setdefault(f"edit_lecturer_{sid}", saved_lect)

                st.session_state[f"edit_majors_{sid}"] = [
                    m for m in st.session_state[f"edit_majors_{sid}"] if m in major_names
                ]

                e_col1, e_col2 = st.columns([1, 2])
                with e_col1:
                    st.text_input("Subject Code:", key=f"edit_code_{sid}")
                with e_col2:
                    st.text_input("Subject Name:", key=f"edit_name_{sid}")

                st.multiselect(
                    "Majors that study this subject (add or remove):",
                    options=major_names,
                    key=f"edit_majors_{sid}"
                )

                e_col3, e_col4, e_col5 = st.columns([1, 1, 1.2])
                with e_col3:
                    st.number_input("Study Time (Hours/Period):", min_value=1, max_value=4, step=1, key=f"edit_hours_{sid}")
                with e_col4:
                    st.selectbox("Required Room Spec:", all_specs, key=f"edit_room_{sid}")
                with e_col5:
                    st.selectbox("Assigned Lecturer:", lecturer_names, key=f"edit_lecturer_{sid}")

                btn_col1, btn_col2 = st.columns(2)
                with btn_col1:
                    st.button("💾 Save Changes", use_container_width=True,
                              on_click=save_subject_edit, args=(save_name, sid))
                with btn_col2:
                    st.button("🗑️ Delete Subject", type="secondary", use_container_width=True,
                              on_click=delete_subject, args=(save_name, sid))

                edit_msg = st.session_state.pop("edit_msg", None)
                if edit_msg:
                    if edit_msg[0] == "success":
                        st.toast(edit_msg[1], icon="💾")
                    getattr(st, edit_msg[0])(edit_msg[1])
        else:
            st.info("No subjects added yet. Add a subject above, then customize it here.")

        st.markdown('</div>', unsafe_allow_html=True)

    # TAB 2: LECTURER ROSTER
    with tab_lects:
        st.markdown('<div class="clean-card">', unsafe_allow_html=True)
        st.subheader("👨‍🏫 Faculty Lecturer Roster")
        st.write("Register academic lecturers to ensure non-overlapping teaching schedules across subjects.")

        l_col1, l_col2 = st.columns([1.5, 1])
        with l_col1:
            new_lect_name = st.text_input("Lecturer Name / Title:", placeholder="e.g. Dr. Somchai W.", key="input_lect_name")
        with l_col2:
            new_lect_dept = st.text_input("Department / Faculty:", placeholder="e.g. Radiological Technology", key="input_lect_dept")

        if st.button("➕ Add Lecturer to Roster", use_container_width=True):
            lect_name_str = new_lect_name.strip()
            dept_str = new_lect_dept.strip() or "General Faculty"

            if not lect_name_str:
                st.error("Please enter a lecturer name.")
            elif any(l["name"].lower() == lect_name_str.lower() for l in data["lecturers"]):
                st.error(f"Lecturer '{lect_name_str}' is already registered in roster!")
            else:
                new_lect = {
                    "id": uuid.uuid4().hex[:8],
                    "name": lect_name_str,
                    "department": dept_str
                }
                data["lecturers"].append(new_lect)
                file1.save_data_to_file(save_name, data)
                st.toast(f"Added lecturer '{lect_name_str}'", icon="👨‍🏫")
                st.success(f"Registered lecturer '{lect_name_str}' ({dept_str}).")
                st.rerun()

        st.markdown('</div>', unsafe_allow_html=True)

        if data["lecturers"]:
            st.markdown('<div class="clean-card">', unsafe_allow_html=True)
            st.subheader("📋 Registered Faculty Members")

            lect_rows = []
            for l in data["lecturers"]:
                assigned_subjs = [
                    f"{s.get('code', '')} {s['name']}".strip() 
                    for s in data["subjects"] if s.get("lecturer") == l["name"]
                ]
                subj_str = ", ".join(assigned_subjs) if assigned_subjs else "None"
                lect_rows.append({
                    "Lecturer Name": l["name"],
                    "Department / Faculty": l.get("department", "General Faculty"),
                    "Assigned Courses": subj_str
                })
            st.table(lect_rows)

            l_del_options = [l["name"] for l in data["lecturers"]]
            l_to_del = st.selectbox("Select Lecturer to Remove:", l_del_options, key="del_lect_select")
            if st.button("🗑️ Delete Lecturer", type="secondary", use_container_width=True):
                data["lecturers"] = [l for l in data["lecturers"] if l["name"] != l_to_del]
                for s in data["subjects"]:
                    if s.get("lecturer") == l_to_del:
                        s["lecturer"] = "Unassigned"
                file1.save_data_to_file(save_name, data)
                st.toast(f"Deleted lecturer '{l_to_del}'", icon="🗑️")
                st.warning(f"Deleted lecturer '{l_to_del}' and reset their assigned subjects to Unassigned.")
                st.rerun()

            st.markdown('</div>', unsafe_allow_html=True)

    # TAB 3: BREAKS & ACTIVITIES
    with tab_breaks:
        st.markdown('<div class="clean-card">', unsafe_allow_html=True)
        st.subheader("☕ Recurring Break & Activity Slots")
        st.write("Specify non-class periods, faculty meetings, lunch breaks, or recurring university activities.")

        b_col1, b_col2, b_col3, b_col4 = st.columns([1.2, 1.2, 1, 1])

        with b_col1:
            break_name = st.text_input("Break / Activity Name:", placeholder="e.g. Lunch Break", key="input_break_name")
        with b_col2:
            scope_options = ["All Majors"] + ([m["name"] for m in data["majors"]] if data["majors"] else [])
            target_scope = st.selectbox("Target Scope:", scope_options, key="select_break_scope")
        with b_col3:
            start_time = st.selectbox("Start Time:", TIME_SLOTS[:-1], index=4, key="select_break_start")
        with b_col4:
            start_idx = TIME_SLOTS.index(start_time)
            valid_end_slots = TIME_SLOTS[start_idx + 1:]
            end_time = st.selectbox("End Time:", valid_end_slots, index=0, key="select_break_end")

        st.write("**Select Applicable Days:**")
        selected_days = st.multiselect(
            "Days of Week (Monday to Sunday):", 
            DAYS_OF_WEEK, 
            default=["Monday", "Tuesday", "Wednesday", "Thursday", "Friday"],
            key="select_break_days"
        )

        st.write("")
        if st.button("➕ Add Break / Activity Slot", use_container_width=True):
            if not break_name.strip():
                st.error("Please enter a valid activity or break name.")
            elif not selected_days:
                st.error("Please select at least one day for the break/activity.")
            else:
                data["breaks"].append({
                    "name": break_name.strip(),
                    "scope": target_scope,
                    "days": selected_days,
                    "start_time": start_time,
                    "end_time": end_time
                })
                file1.save_data_to_file(save_name, data)
                st.toast(f"Added break slot '{break_name.strip()}'", icon="☕")
                st.success(f"Added break '{break_name.strip()}' ({start_time} - {end_time}) on {', '.join(selected_days)}.")
                st.rerun()

        st.markdown('</div>', unsafe_allow_html=True)

        st.markdown('<div class="clean-card">', unsafe_allow_html=True)
        st.subheader("📋 Configured Breaks & Activities")

        if data["breaks"]:
            break_table = []
            for b in data["breaks"]:
                break_table.append({
                    "Activity / Break Name": b["name"],
                    "Target Scope": b.get("scope", "All Majors"),
                    "Applicable Days": ", ".join(b["days"]),
                    "Time Window": f"{b['start_time']} - {b['end_time']}"
                })
            st.table(break_table)

            b_del_options = [f"{b['name']} ({b['start_time']}-{b['end_time']})" for b in data["breaks"]]
            b_to_del_idx = st.selectbox("Select Break/Activity to Remove:", range(len(b_del_options)), format_func=lambda i: b_del_options[i], key="del_break_select")

            if st.button("🗑️ Delete Selected Activity Slot", type="secondary"):
                del_item = data["breaks"].pop(b_to_del_idx)
                file1.save_data_to_file(save_name, data)
                st.toast(f"Deleted break slot '{del_item['name']}'", icon="🗑️")
                st.warning(f"Deleted break/activity '{del_item['name']}'.")
                st.rerun()
        else:
            st.info("No recurring breaks or activities configured yet.")

        st.markdown('</div>', unsafe_allow_html=True)

    st.write("")
    nav_col1, nav_col2 = st.columns(2)
    with nav_col1:
        if st.button("← Back to Step 2 (Map & Room Customization)", type="secondary"):
            st.session_state.current_page = "file2"
            st.rerun()
    with nav_col2:
        if st.button("Proceed to Step 4 (Timetable Output) →"):
            st.session_state.current_page = "file4"
            st.rerun()
