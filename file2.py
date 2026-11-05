import uuid
import file1
import matplotlib
import matplotlib.pyplot as plt
import networkx as nx
import streamlit as st

matplotlib.use('Agg')

# Set font family globally
plt.rcParams['font.sans-serif'] = ['Chulabhorn Likit Text', 'Prompt', 'DejaVu Sans', 'sans-serif']
plt.rcParams['font.family'] = 'sans-serif'

DEFAULT_ROOM_SPECS = [
    "For Anatomy Class",
    "General Lecture",
    "Laboratory",
    "Radiological Technology School",
    "Human Kinetics and Health School",
    "Paramedic School"
]

EDIT_PREFIXES = (
    "edit_rm_bld_",
    "edit_rm_name_",
    "edit_rm_cap_",
    "edit_rm_spec_"
)

def get_all_specs(data):
    custom = data.get("custom_specs", [])
    specs = list(DEFAULT_ROOM_SPECS)
    for c in custom:
        if c not in specs:
            specs.append(c)
    return specs

def ensure_room_fields(data):
    data.setdefault("rooms", [])
    changed = False
    for r in data["rooms"]:
        if "id" not in r:
            r["id"] = uuid.uuid4().hex[:8]
            changed = True
    return changed

def find_room(data, rid):
    for r in data["rooms"]:
        if r.get("id") == rid:
            return r
    return None

def clear_room_edit_state(rid):
    for prefix in EDIT_PREFIXES:
        st.session_state.pop(prefix + rid, None)

def room_label(r):
    return f"{r['building']} - {r['name']} ({r['capacity']} seats, {r['usage']})"

def calculate_mst(nodes, edges):
    if not nodes or not edges:
        return [], 0, False
        
    G = nx.Graph()
    for n in nodes:
        G.add_node(n["name"])
        
    for e in edges:
        try:
            G.add_edge(e["from"], e["to"], weight=float(e["distance"]))
        except (ValueError, TypeError, KeyError):
            continue
        
    is_connected = nx.is_connected(G) if len(nodes) > 1 else True
    
    mst_edges = []
    total_distance = 0.0
    
    try:
        mst_graph = nx.minimum_spanning_tree(G)
        for u, v, d in mst_graph.edges(data=True):
            dist = d.get('weight', 0.0)
            mst_edges.append({
                "from": u,
                "to": v,
                "distance": dist
            })
            total_distance += dist
    except Exception:
        mst_edges = []
        total_distance = 0.0
        is_connected = False
        
    return mst_edges, total_distance, is_connected

def draw_network_graph(nodes, edges, mst_edges):
    raw_theme = st.session_state.get("app_theme") if "st" in globals() and hasattr(st, "session_state") else None
    theme = str(raw_theme) if raw_theme else "🌌 Midnight Glassmorphism"
    is_light = ("Pearl Silver" in theme or "slate" in theme.lower())

    fig_bg = '#FFFFFF' if is_light else '#0B0F19'
    edge_normal = '#CBD5E1' if is_light else '#475569'
    edge_mst = '#EF4444' if is_light else '#FF4D4D'
    
    fig, ax = plt.subplots(figsize=(8.5, 5.5), facecolor=fig_bg)
    ax.set_facecolor(fig_bg)
    
    if not nodes:
        ax.text(0.5, 0.5, "No building nodes added yet", 
                ha='center', va='center', fontsize=14, color='#94A3B8')
        ax.axis('off')
        return fig
        
    G = nx.Graph()
    for n in nodes:
        node_name = str(n.get("name", "")).strip()
        if node_name:
            G.add_node(node_name)
        
    edge_weights = {}
    for e in edges:
        try:
            u = str(e.get("from", "")).strip()
            v = str(e.get("to", "")).strip()
            dist = float(e.get("distance", 0))
            if u and v:
                G.add_edge(u, v, weight=dist)
                w_val = int(dist) if dist == int(dist) else dist
                edge_weights[(u, v)] = f"{w_val}m"
        except (ValueError, TypeError, KeyError):
            continue

    if len(G.nodes) == 0:
        ax.text(0.5, 0.5, "No valid building nodes", 
                ha='center', va='center', fontsize=14, color='#94A3B8')
        ax.axis('off')
        return fig

    pos = nx.spring_layout(G, seed=42, k=1.3) if len(G.nodes) > 1 else {list(G.nodes)[0]: (0, 0)}
    
    mst_set = set()
    for me in mst_edges:
        try:
            u = str(me.get("from", "")).strip()
            v = str(me.get("to", "")).strip()
            if u and v:
                mst_set.add(tuple(sorted([u, v])))
        except Exception:
            continue
        
    normal_edges = []
    highlight_mst_edges = []
    
    for u, v in G.edges():
        pair = tuple(sorted([u, v]))
        if pair in mst_set:
            highlight_mst_edges.append((u, v))
        else:
            normal_edges.append((u, v))
            
    if normal_edges:
        nx.draw_networkx_edges(G, pos, edgelist=normal_edges, ax=ax, edge_color=edge_normal, width=2, style='dashed')
    if highlight_mst_edges:
        nx.draw_networkx_edges(G, pos, edgelist=highlight_mst_edges, ax=ax, edge_color=edge_mst, width=4)
    
    # Custom Edge Weights Box (Hex colors only, no CSS rgba syntax)
    for (u, v), label in edge_weights.items():
        if u not in pos or v not in pos:
            continue
        pair = tuple(sorted([u, v]))
        x = (pos[u][0] + pos[v][0]) / 2
        y = (pos[u][1] + pos[v][1]) / 2
        
        is_mst = pair in mst_set
        
        if is_light:
            bbox_color = "#FEF2F2" if is_mst else "#F1F5F9"
            text_color = "#DC2626" if is_mst else "#475569"
            border_color = "#FCA5A5" if is_mst else "#CBD5E1"
        else:
            bbox_color = "#7F1D1D" if is_mst else "#1E293B"
            text_color = "#FCA5A5" if is_mst else "#38BDF8"
            border_color = "#EF4444" if is_mst else "#0284C7"
        
        ax.text(x, y, f" {label} ", fontsize=8.5, fontweight='bold', color=text_color,
                ha='center', va='center',
                bbox=dict(boxstyle="round,pad=0.35", facecolor=bbox_color, edgecolor=border_color, linewidth=1.2))

    # Custom Node Bounding Box Fill around Building Names
    for n, (x, y) in pos.items():
        if is_light:
            box_fill = "#0F172A"
            box_stroke = "#38BDF8"
            text_col = "#FFFFFF"
        else:
            box_fill = "#1E1B4B"
            box_stroke = "#38BDF8"
            text_col = "#FFFFFF"

        ax.scatter(x, y, s=650, color=box_fill, zorder=4)
        ax.text(x, y - 0.12, f"  {n}  ", fontsize=9.5, fontweight='bold', color=text_col,
                ha='center', va='center', zorder=5,
                bbox=dict(boxstyle="round,pad=0.4", facecolor=box_fill, edgecolor=box_stroke, linewidth=1.5))
    
    ax.axis('off')
    plt.tight_layout()
    return fig

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
    
    data.setdefault("nodes", [])
    data.setdefault("edges", [])
    data.setdefault("rooms", [])
    data.setdefault("custom_specs", [])
    
    if ensure_room_fields(data):
        file1.save_data_to_file(save_name, data)
    
    st.markdown(f'<div class="brand-badge">📍 Step 2 Workspace | Save: {save_name}</div>', unsafe_allow_html=True)
    st.markdown('<div class="schedpath-title" style="font-size: 2.3rem;">Map & Room Customization</div>', unsafe_allow_html=True)
    st.markdown('<div class="schedpath-subtitle">Configure campus building nodes, inter-building distances, calculate MST routes, and set room capacities & specs.</div>', unsafe_allow_html=True)
    
    tab1, tab2 = st.tabs(["🗺️ 3. Map Customization & MST", "🏫 4. Room Size & Capacity"])
    
    # ==========================================
    # TAB 1: MAP CUSTOMIZATION & MST
    # ==========================================
    with tab1:
        col_ctrl, col_viz = st.columns([1, 1.2])
        
        with col_ctrl:
            st.markdown('<div class="clean-card">', unsafe_allow_html=True)
            st.subheader("🏢 Building Nodes Management")
            
            node_input_col1, node_input_col2 = st.columns([2, 1])
            with node_input_col1:
                new_building = st.text_input("New Building Name:", placeholder="e.g. Building A", key="new_bld_input")
            with node_input_col2:
                st.write("")
                st.write("")
                if st.button("Add Building", use_container_width=True):
                    if not new_building.strip():
                        st.error("Please enter a valid building name.")
                    elif any(n["name"] == new_building.strip() for n in data["nodes"]):
                        st.error("Building already exists!")
                    else:
                        data["nodes"].append({"id": new_building.strip(), "name": new_building.strip()})
                        file1.save_data_to_file(save_name, data)
                        st.toast(f"Added building '{new_building.strip()}'", icon="🏢")
                        st.success(f"Added building '{new_building.strip()}'.")
                        st.rerun()
            
            if data["nodes"]:
                existing_node_names = [n["name"] for n in data["nodes"]]
                del_node_col1, del_node_col2 = st.columns([2, 1])
                with del_node_col1:
                    node_to_del = st.selectbox("Select Building to Delete:", existing_node_names, key="del_bld_select")
                with del_node_col2:
                    st.write("")
                    st.write("")
                    if st.button("Delete Node", type="secondary", use_container_width=True):
                        data["nodes"] = [n for n in data["nodes"] if n["name"] != node_to_del]
                        data["edges"] = [e for e in data["edges"] if e["from"] != node_to_del and e["to"] != node_to_del]
                        data["rooms"] = [r for r in data["rooms"] if r["building"] != node_to_del]
                        file1.save_data_to_file(save_name, data)
                        st.toast(f"Deleted building '{node_to_del}'", icon="🗑️")
                        st.warning(f"Deleted building '{node_to_del}'.")
                        st.rerun()
            else:
                st.info("No building nodes added yet. Add your first building above.")
                
            st.markdown('</div>', unsafe_allow_html=True)
            
            st.markdown('<div class="clean-card">', unsafe_allow_html=True)
            st.subheader("📏 Inter-Building Distances")
            
            if len(data["nodes"]) >= 2:
                bld_names = [n["name"] for n in data["nodes"]]
                
                dist_col1, dist_col2, dist_col3 = st.columns([1, 1, 1])
                with dist_col1:
                    bld_from = st.selectbox("From Building:", bld_names, key="dist_from")
                with dist_col2:
                    to_options = [b for b in bld_names if b != bld_from]
                    bld_to = st.selectbox("To Building:", to_options, key="dist_to")
                with dist_col3:
                    dist_val = st.number_input("Distance (meters):", min_value=1.0, value=100.0, step=10.0, key="dist_val")
                    
                if st.button("➕ Add / Update Distance", use_container_width=True):
                    found = False
                    for e in data["edges"]:
                        if (e["from"] == bld_from and e["to"] == bld_to) or (e["from"] == bld_to and e["to"] == bld_from):
                            e["distance"] = dist_val
                            found = True
                            break
                    if not found:
                        data["edges"].append({"from": bld_from, "to": bld_to, "distance": dist_val})
                        
                    file1.save_data_to_file(save_name, data)
                    st.toast(f"Updated distance {bld_from} ↔ {bld_to}: {dist_val}m", icon="📏")
                    st.success(f"Set distance between {bld_from} and {bld_to} to {dist_val}m.")
                    st.rerun()
                    
                if data["edges"]:
                    st.write("**Existing Distances:**")
                    for idx, e in enumerate(data["edges"]):
                        ecol1, ecol2 = st.columns([3, 1])
                        with ecol1:
                            st.write(f"• **{e['from']}** ↔ **{e['to']}**: `{e['distance']} meters`")
                        with ecol2:
                            if st.button("Remove", key=f"del_edge_{idx}", type="secondary", use_container_width=True):
                                data["edges"].pop(idx)
                                file1.save_data_to_file(save_name, data)
                                st.rerun()
            else:
                st.info("Add at least 2 building nodes to configure inter-building distances.")
                
            st.markdown('</div>', unsafe_allow_html=True)
            
        with col_viz:
            st.markdown('<div class="clean-card">', unsafe_allow_html=True)
            st.subheader("🌲 Campus Network & Minimum Spanning Tree")
            
            mst_edges, total_dist, is_connected = calculate_mst(data["nodes"], data["edges"])
            data["mst_edges"] = mst_edges
            file1.save_data_to_file(save_name, data)
            
            mcol1, mcol2 = st.columns(2)
            with mcol1:
                st.metric("Total MST Distance", f"{total_dist:.1f} m")
            with mcol2:
                status_str = "Connected" if is_connected else "Disconnected"
                st.metric("Network Connectivity", status_str)
                
            st.caption("🔴 **Highlighted Edges**: Minimum Spanning Tree (MST) routes | 🌫️ **Dashed Edges**: Standard paths")
            
            fig = draw_network_graph(data["nodes"], data["edges"], mst_edges)
            st.pyplot(fig)
            
            if mst_edges:
                st.write("**Selected MST Path Connections:**")
                for me in mst_edges:
                    st.markdown(f"- 🔴 **{me['from']}** ↔ **{me['to']}**: `{me['distance']} meters`")
            elif data["nodes"]:
                st.info("Add connections between buildings to form the MST route.")
                
            st.markdown('</div>', unsafe_allow_html=True)

    # ==========================================
    # TAB 2: ROOM SIZE & CAPACITY
    # ==========================================
    with tab2:
        st.markdown('<div class="clean-card">', unsafe_allow_html=True)
        st.subheader("🏷️ Custom Room Specifications")
        st.write("Add custom room usage specs beyond defaults (e.g. 'Simulation Lab', 'X-Ray Room').")
        
        spec_col1, spec_col2 = st.columns([2, 1])
        with spec_col1:
            new_custom_spec = st.text_input("New Custom Spec Name:", placeholder="e.g. Simulation Laboratory", key="input_new_custom_spec")
        with spec_col2:
            st.write("")
            st.write("")
            if st.button("➕ Add Custom Spec", use_container_width=True):
                spec_str = new_custom_spec.strip()
                all_current = get_all_specs(data)
                if not spec_str:
                    st.error("Please enter a valid spec name.")
                elif spec_str.lower() in [s.lower() for s in all_current]:
                    st.error(f"Specification '{spec_str}' already exists!")
                else:
                    data.setdefault("custom_specs", [])
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
                    if st.button("Remove", key=f"del_cspec_{idx}", type="secondary", use_container_width=True):
                        data["custom_specs"].pop(idx)
                        file1.save_data_to_file(save_name, data)
                        st.rerun()
                        
        st.markdown('</div>', unsafe_allow_html=True)

        st.markdown('<div class="clean-card">', unsafe_allow_html=True)
        st.subheader("➕ Add Room to Building")
        
        all_specs = get_all_specs(data)
        
        if data["nodes"]:
            bld_list = [n["name"] for n in data["nodes"]]
            
            rcol1, rcol2, rcol3, rcol4 = st.columns([1.2, 1.2, 1, 1])
            with rcol1:
                target_bld = st.selectbox("Building:", bld_list, key="rm_target_bld")
            with rcol2:
                room_name = st.text_input("Room Name / Number:", placeholder="e.g. Room 101", key="rm_name")
            with rcol3:
                room_cap = st.number_input("Capacity (Students):", min_value=1, value=40, step=5, key="rm_cap")
            with rcol4:
                room_usage = st.selectbox("Room Usage / Specs:", all_specs, key="rm_usage")
                
            if st.button("➕ Add Room", use_container_width=True):
                if not room_name.strip():
                    st.error("Please enter a room name.")
                elif any(r["building"] == target_bld and r["name"].strip().lower() == room_name.strip().lower() for r in data["rooms"]):
                    st.error(f"Room '{room_name.strip()}' already exists in {target_bld}!")
                else:
                    new_room = {
                        "id": uuid.uuid4().hex[:8],
                        "building": target_bld,
                        "name": room_name.strip(),
                        "capacity": int(room_cap),
                        "usage": room_usage
                    }
                    data["rooms"].append(new_room)
                    file1.save_data_to_file(save_name, data)
                    st.toast(f"Added room '{room_name.strip()}' to {target_bld}", icon="🏫")
                    st.success(f"Added '{room_name.strip()}' to {target_bld}.")
                    st.rerun()
        else:
            st.info("Please add at least one building node in the Map tab first.")
            
        st.markdown('</div>', unsafe_allow_html=True)

        if data["rooms"]:
            st.markdown('<div class="clean-card">', unsafe_allow_html=True)
            st.subheader("🛠️ Edit Room Configuration (Size & Spec)")

            room_ids = [r["id"] for r in data["rooms"]]
            label_map = {r["id"]: room_label(r) for r in data["rooms"]}

            if st.session_state.get("edit_rm_select") not in room_ids:
                st.session_state.pop("edit_rm_select", None)

            rid = st.selectbox(
                "Select Room to Edit:",
                room_ids,
                format_func=lambda i: label_map.get(i, i),
                key="edit_rm_select"
            )

            room_obj = find_room(data, rid)

            if room_obj:
                bld_list = [n["name"] for n in data["nodes"]]
                all_specs = get_all_specs(data)

                saved_bld = room_obj["building"] if room_obj["building"] in bld_list else (bld_list[0] if bld_list else "")
                saved_spec = room_obj["usage"] if room_obj["usage"] in all_specs else (all_specs[0] if all_specs else "General Lecture")

                st.session_state.setdefault(f"edit_rm_bld_{rid}", saved_bld)
                st.session_state.setdefault(f"edit_rm_name_{rid}", room_obj["name"])
                st.session_state.setdefault(f"edit_rm_cap_{rid}", int(room_obj["capacity"]))
                st.session_state.setdefault(f"edit_rm_spec_{rid}", saved_spec)

                ecol1, ecol2, ecol3, ecol4 = st.columns([1.2, 1.2, 1, 1])
                with ecol1:
                    st.selectbox("Building:", bld_list, key=f"edit_rm_bld_{rid}")
                with ecol2:
                    st.text_input("Room Name:", key=f"edit_rm_name_{rid}")
                with ecol3:
                    st.number_input("Capacity (Seats):", min_value=1, step=5, key=f"edit_rm_cap_{rid}")
                with ecol4:
                    st.selectbox("Room Usage / Spec:", all_specs, key=f"edit_rm_spec_{rid}")

                btn_r1, btn_r2 = st.columns(2)
                with btn_r1:
                    if st.button("💾 Save Room Changes", use_container_width=True):
                        new_bld = st.session_state.get(f"edit_rm_bld_{rid}", room_obj["building"])
                        new_name = st.session_state.get(f"edit_rm_name_{rid}", "").strip()
                        new_cap = int(st.session_state.get(f"edit_rm_cap_{rid}", room_obj["capacity"]))
                        new_spec = st.session_state.get(f"edit_rm_spec_{rid}", room_obj["usage"])

                        if not new_name:
                            st.error("Room name cannot be empty.")
                        else:
                            duplicate = False
                            for other in data["rooms"]:
                                if other["id"] == rid:
                                    continue
                                if other["building"] == new_bld and other["name"].strip().lower() == new_name.lower():
                                    duplicate = True
                                    break
                            
                            if duplicate:
                                st.error(f"Another room named '{new_name}' already exists in {new_bld}.")
                            else:
                                room_obj["building"] = new_bld
                                room_obj["name"] = new_name
                                room_obj["capacity"] = new_cap
                                room_obj["usage"] = new_spec
                                
                                clear_room_edit_state(rid)
                                file1.save_data_to_file(save_name, data)
                                st.toast(f"Saved changes to '{new_name}'", icon="💾")
                                st.success(f"Saved changes to room '{new_name}' ({new_bld}).")
                                st.rerun()

                with btn_r2:
                    if st.button("🗑️ Delete Selected Room", type="secondary", use_container_width=True):
                        data["rooms"] = [r for r in data["rooms"] if r["id"] != rid]
                        clear_room_edit_state(rid)
                        st.session_state.pop("edit_rm_select", None)
                        file1.save_data_to_file(save_name, data)
                        st.toast(f"Deleted room '{room_obj['name']}'", icon="🗑️")
                        st.warning(f"Deleted room '{room_obj['name']}' from {room_obj['building']}.")
                        st.rerun()

            st.markdown('</div>', unsafe_allow_html=True)

        col_tbl1, col_tbl2 = st.columns([1.3, 1])
        
        with col_tbl1:
            st.markdown('<div class="clean-card">', unsafe_allow_html=True)
            st.subheader("📋 All Configured Rooms")
            
            if data["rooms"]:
                table_data = []
                for r in data["rooms"]:
                    table_data.append({
                        "Building": r["building"],
                        "Room Name": r["name"],
                        "Capacity": f"{r['capacity']} seats",
                        "Usage Constraint": r["usage"]
                    })
                st.table(table_data)
            else:
                st.info("No rooms added yet. Use the form above to register rooms for each building.")
            st.markdown('</div>', unsafe_allow_html=True)
            
        with col_tbl2:
            st.markdown('<div class="clean-card">', unsafe_allow_html=True)
            st.subheader("📊 Building Capacity Summary")
            
            if data["nodes"]:
                summary_data = []
                total_campus_capacity = 0
                total_rooms_count = 0
                
                for n in data["nodes"]:
                    bld_rooms = [r for r in data["rooms"] if r["building"] == n["name"]]
                    bld_cap = sum(r["capacity"] for r in bld_rooms)
                    total_campus_capacity += bld_cap
                    total_rooms_count += len(bld_rooms)
                    
                    summary_data.append({
                        "Building": n["name"],
                        "Total Rooms": len(bld_rooms),
                        "Total Capacity": f"{bld_cap} seats"
                    })
                    
                st.table(summary_data)
                
                scol1, scol2 = st.columns(2)
                with scol1:
                    st.metric("Total Campus Rooms", f"{total_rooms_count}")
                with scol2:
                    st.metric("Total Campus Seat Capacity", f"{total_campus_capacity} seats")
            else:
                st.info("No buildings configured.")
            st.markdown('</div>', unsafe_allow_html=True)
            
    st.write("")
    nav_col1, nav_col2 = st.columns(2)
    with nav_col1:
        if st.button("← Back to Step 1 (Save Management)", type="secondary"):
            st.session_state.current_page = "file1"
            st.rerun()
    with nav_col2:
        if st.button("Proceed to Step 3 (Curriculum & Faculty) →"):
            st.session_state.current_page = "file3"
            st.rerun()
