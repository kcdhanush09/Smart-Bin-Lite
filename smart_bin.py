import streamlit as st
import networkx as nx
import matplotlib.pyplot as plt
import random
import math

# --- CONFIGURATION ---
st.set_page_config(page_title="Smart bin Lite Simulator", layout="wide")

# --- HEADER ---
st.title("♻️ Smart bin Lite: Solid Waste Route Optimizer")
st.markdown("""
**Project by:** G Muni Pranathi, KC Dhanush, P Vedavyas Reddy  
**Advisor:** Dr. Brindha Moorthy, IIT Tirupati  
*A simulation to validate the benefits of dynamic routing over static scheduling.*
""")
st.markdown("---")

# --- SIDEBAR: SIMULATION CONTROLS ---
st.sidebar.header("⚙️ Simulation Controls")

# Phase I: Graph Modeling Inputs 
num_bins = st.sidebar.slider("Number of Bins (Nodes)", min_value=5, max_value=20, value=10)
depot_node = 0  # Node 0 is always the starting Depot

# Phase II: Simulation Inputs [cite: 31, 36]
fill_threshold = st.sidebar.slider("Operational Threshold (T%)", min_value=0, max_value=100, value=75, 
                                   help="Bins filled above this percentage are considered 'Critical'.")

if st.sidebar.button("🔄 Regenerate City Layout"):
    st.session_state.seed = random.randint(1, 1000)

# Initialize Session State for persistence
if 'seed' not in st.session_state:
    st.session_state.seed = 42

random.seed(st.session_state.seed)

# --- PHASE I: GRAPH MODELING [cite: 24, 25, 27, 28] ---
# Creating a random geometric graph to simulate a city layout
# Nodes = Physical Locations, Edges = Roads, Weights = Distance
G = nx.random_geometric_graph(num_bins, radius=0.4, seed=st.session_state.seed)
pos = nx.get_node_attributes(G, 'pos')

# Ensure graph is connected for routing
G = nx.complete_graph(num_bins) # Using complete graph to ensure all nodes are reachable
for (u, v) in G.edges():
    # Calculate Euclidean distance as weight
    dist = math.sqrt((pos[u][0] - pos[v][0])**2 + (pos[u][1] - pos[v][1])**2)
    G.edges[u, v]['weight'] = dist

# --- PHASE II: DATA SIMULATION & FILTERING  ---

# 1. Real-Time Fill-Level Simulation [cite: 31]
# Assign random fill levels (0-100%) to all bins except Depot (Node 0)
node_fill_levels = {0: 0} # Depot has 0 garbage
for i in range(1, num_bins):
    node_fill_levels[i] = random.randint(0, 100)

# 2. The Critical Bin Filter [cite: 35]
# Critical Set C = { B_i | L_Fill > T }
critical_bins = [0] # Depot is always critical (start/end)
for node, fill in node_fill_levels.items():
    if node != 0 and fill > fill_threshold:
        critical_bins.append(node)

# --- PHASE III: ALGORITHM - DRIVEN OPTIMIZATION [cite: 37, 39, 40] ---

def calculate_route_distance(graph, route):
    """Calculates total distance of a given sequence of nodes."""
    total_dist = 0
    for i in range(len(route) - 1):
        u, v = route[i], route[i+1]
        total_dist += graph[u][v]['weight']
    return total_dist * 100  # Scaling up for display (e.g., meters/km)

def get_greedy_route(graph, nodes_to_visit):
    """
    Simplified TSP Approximation [cite: 39]
    Uses 'Nearest Neighbor' heuristic driven by shortest path.
    """
    unvisited = nodes_to_visit.copy()
    unvisited.remove(0) # Remove depot
    current_node = 0
    route = [0]
    
    while unvisited:
        # Find nearest available node using Dijkstra/Weight
        nearest_node = min(unvisited, key=lambda x: graph[current_node][x]['weight'])
        route.append(nearest_node)
        unvisited.remove(nearest_node)
        current_node = nearest_node
        
    route.append(0) # Return to depot
    return route

# 1. Static Route (Traditional): Visits ALL bins sequentially
static_route = list(range(num_bins)) + [0]
dist_static = calculate_route_distance(G, static_route)

# 2. Dynamic Route (Optimized): Visits ONLY Critical Bins using Greedy TSP
dynamic_route = get_greedy_route(G, critical_bins)
dist_dynamic = calculate_route_distance(G, dynamic_route)

# 3. Calculate Efficiency Saving [cite: 41]
if dist_static > 0:
    efficiency_saving = ((dist_static - dist_dynamic) * 100) / dist_static
else:
    efficiency_saving = 0

# --- DASHBOARD VISUALIZATION ---

col1, col2 = st.columns([3, 1])

with col1:
    st.subheader("📍 Live Route Visualization")
    
    # Setup Plot
    fig, ax = plt.subplots(figsize=(10, 6))
    
    # Draw all edges (Roads) faintly
    nx.draw_networkx_edges(G, pos, alpha=0.1, edge_color='gray')
    
    # Draw Nodes (Bins)
    # Color logic: Red = Critical (>T), Green = Safe (<T), Blue = Depot
    node_colors = []
    for i in G.nodes():
        if i == 0:
            node_colors.append('blue') # Depot
        elif i in critical_bins:
            node_colors.append('red') # Critical
        else:
            node_colors.append('green') # Non-critical
            
    nx.draw_networkx_nodes(G, pos, node_color=node_colors, node_size=500)
    nx.draw_networkx_labels(G, pos, font_color='white')
    
    # Draw Optimized Path (The Solution)
    path_edges = list(zip(dynamic_route, dynamic_route[1:]))
    nx.draw_networkx_edges(G, pos, edgelist=path_edges, edge_color='blue', width=2, style='dashed')
    
    st.pyplot(fig)
    
    st.caption("Map Legend: 🔵 Depot | 🔴 Critical Bin (Must Visit) | 🟢 Non-Critical Bin (Skip) | 🔹 Blue Path: Optimized Route")

with col2:
    st.subheader("📊 Validation Metrics")
    
    st.metric(label="♻️ Efficiency Savings", value=f"{efficiency_saving:.2f}%", delta="Reduction in Travel")
    
    st.markdown("### Distance Comparison")
    st.write(f"**Static Route:** {dist_static:.1f} km")
    st.write(f"**Dynamic Route:** {dist_dynamic:.1f} km")
    
    st.markdown("### Bin Status")
    st.write(f"Total Bins: **{num_bins}**")
    st.write(f"Critical Bins: **{len(critical_bins)-1}**")
    
    st.markdown("---")
    st.info("The 'Efficiency Saving' metric validates the proposed methodology by proving a measurable reduction in distance[cite: 20].")

# --- DATA TABLE ---
st.subheader("📋 Bin Status Data (Simulated)")
status_data = []
for node in range(num_bins):
    status = "CRITICAL" if node in critical_bins and node != 0 else "Normal"
    if node == 0: status = "DEPOT"
    status_data.append({
        "Bin ID": node, 
        "Fill Level (%)": node_fill_levels[node], 
        "Status": status,
        "Action": "Collect" if node in dynamic_route else "Skip"
    })
st.dataframe(status_data)