import streamlit as st
import networkx as nx
import matplotlib.pyplot as plt
import pandas as pd

# --- CONFIGURACIÓN DE LA PÁGINA ---
st.set_page_config(page_title="Mario's Star Path Finder", page_icon="??", layout="wide")

INF = float('inf')

# --- LÓGICA DEL ALGORITMO ---
@st.cache_data 
def calcular_floyd_warshall(grafo):
    V = len(grafo)
    C = [[grafo[i][j] for j in range(V)] for i in range(V)]
    Z = [[None for _ in range(V)] for _ in range(V)]
    for i in range(V):
        for j in range(V):
            if i != j and grafo[i][j] != INF:
                Z[i][j] = j
    for k in range(V):
        for i in range(V):
            for j in range(V):
                if C[i][k] + C[k][j] < C[i][j]:
                    C[i][j] = C[i][k] + C[k][j]
                    Z[i][j] = Z[i][k]
    return C, Z

def obtener_ruta_lista(Z, inicio, destino):
    if Z[inicio][destino] is None: return []
    ruta = [inicio]
    actual = inicio
    while actual != destino:
        actual = Z[actual][destino]
        if actual is None: return []
        ruta.append(actual)
    return ruta

# --- DATOS DEL GRAFO ---
grafo_mario = [
    [0,   5,   INF, 10,  INF],
    [INF, 0,   3,   INF, 11],
    [INF, INF, 0,   1,   7],
    [INF, INF, 15,  0,   2],
    [4,   INF, INF, INF, 0]
]
num_nodos = len(grafo_mario)
nombres_mundos = [f"Mundo {i} (Warp Zone)" if i == 1 else f"Mundo {i}" for i in range(num_nodos)]
nombres_mundos[0] = "Mundo 0 (Inicio)"
nombres_mundos[-1] = "Mundo Final ??"

# --- INTERFAZ WEB ---
st.title("?? Mario's Star Path Finder ??")
st.markdown("¡Encuentra la ruta más rápida entre los mundos del Reino Champiñón usando el **Algoritmo de Floyd-Warshall**!")

col1, col2 = st.columns([1, 2])

with col1:
    st.header("?? Controles de Navegación")
    
    origen = st.selectbox("?? Punto de Partida:", nombres_mundos, index=0)
    destino = st.selectbox("?? Destino Final:", nombres_mundos, index=len(nombres_mundos)-1)
    
    idx_origen = nombres_mundos.index(origen)
    idx_destino = nombres_mundos.index(destino)

    st.markdown("---")
    
    matriz_C, matriz_Z = calcular_floyd_warshall(grafo_mario)
    ruta = obtener_ruta_lista(matriz_Z, idx_origen, idx_destino)
    costo = matriz_C[idx_origen][idx_destino]

    st.subheader("?? Resultados")
    if costo == INF:
        st.error("¡Mamma Mia! No hay un camino posible entre estos mundos.")
    else:
        st.metric(label="Costo Total del Viaje", value=f"{costo} Monedas ??")
        nombres_ruta = [f"W{i}" for i in ruta]
        st.success(f"**Ruta óptima:** {' ? '.join(nombres_ruta)}")

with col2:
    tab_mapa, tab_matrices = st.tabs(["??? Mapa Visual", "?? Matrices Matemáticas"])
    
    with tab_mapa:
        fig, ax = plt.subplots(figsize=(6, 4))
        G = nx.DiGraph()
        for i in range(num_nodos):
            G.add_node(i)
            for j in range(num_nodos):
                if grafo_mario[i][j] != 0 and grafo_mario[i][j] != INF:
                    G.add_edge(i, j, weight=grafo_mario[i][j])
        
        pos = nx.circular_layout(G)
        nx.draw_networkx_nodes(G, pos, ax=ax, node_color="#5C94FC", node_size=800, edgecolors="black")
        nx.draw_networkx_labels(G, pos, ax=ax, font_color="white", font_weight="bold")
        nx.draw_networkx_edges(G, pos, ax=ax, edge_color="gray", arrows=True, connectionstyle="arc3,rad=0.1")
        
        labels = nx.get_edge_attributes(G, 'weight')
        nx.draw_networkx_edge_labels(G, pos, ax=ax, edge_labels=labels, font_size=9)

        if ruta:
            aristas_ruta = [(ruta[i], ruta[i+1]) for i in range(len(ruta)-1)]
            nx.draw_networkx_nodes(G, pos, ax=ax, nodelist=ruta, node_color="#E52521", node_size=900)
            nx.draw_networkx_edges(G, pos, ax=ax, edgelist=aristas_ruta, edge_color="#43B047", width=3, arrows=True, connectionstyle="arc3,rad=0.1")

        ax.axis('off')
        st.pyplot(fig)

    with tab_matrices:
        st.markdown("### Matriz C (Costos Mínimos)")
        df_c = pd.DataFrame(matriz_C).replace(INF, "INF")
        st.dataframe(df_c, use_container_width=True)

        st.markdown("### Matriz Z (Siguiente Salto)")
        df_z = pd.DataFrame(matriz_Z).fillna("-")
        st.dataframe(df_z, use_container_width=True)