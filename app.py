import streamlit as st
import networkx as nx
import matplotlib.pyplot as plt
import pandas as pd
import copy

# --- CONFIGURACIÓN DE LA PÁGINA ---
st.set_page_config(page_title="Mario's Star Path Finder", page_icon="🍄", layout="wide")

INF = float('inf')

# --- DEFINICIÓN DE LOS NIVELES (GRAFOS) ---
# Nivel 1: El ejemplo de clase (6 nodos)
grafo_clase = [
    [0,   3, INF, INF, INF,   2],
    [INF, 0,  -1, INF, INF,   0],
    [INF, INF, 0,  -2, INF,   5],
    [INF, INF, INF, 0, INF,   5],
    [1,   INF, INF, 8,   0, INF],
    [INF, INF, INF, INF, 5,   0]
]

# Nivel 2: Desierto Pirámide (4 nodos - Rápido y engañoso)
grafo_desierto = [
    [0,   8, INF,  1],
    [INF, 0,   1, INF],
    [4,  INF,  0, INF],
    [INF, 2,   9,  0]
]

# Nivel 3: Castillo de Bowser (5 nodos - Con pesos negativos y atajos)
grafo_castillo = [
    [0,   3,   8, INF, -4],
    [INF, 0, INF,   1,  7],
    [INF, 4,   0, INF, INF],
    [2,  INF, -5,   0, INF],
    [INF, INF, INF, 6,  0]
]

diccionario_niveles = {
    "Nivel 1: Ejemplo de Clase (6 Mundos)": grafo_clase,
    "Nivel 2: Desierto Pirámide (4 Mundos)": grafo_desierto,
    "Nivel 3: Castillo de Bowser (5 Mundos)": grafo_castillo
}

# --- LÓGICA DEL ALGORITMO CON ITERACIONES ---
@st.cache_data 
def calcular_floyd_warshall_paso_a_paso(grafo):
    V = len(grafo)
    C = [[grafo[i][j] for j in range(V)] for i in range(V)]
    Z = [[None for _ in range(V)] for _ in range(V)]
    
    # Inicialización de Z
    for i in range(V):
        for j in range(V):
            if i != j and grafo[i][j] != INF:
                Z[i][j] = j
                
    iteraciones = [] # Aquí guardaremos el historial
    
    # Estado inicial k = -1 (Antes de empezar)
    iteraciones.append(("Estado Inicial", copy.deepcopy(C), copy.deepcopy(Z)))

    for k in range(V):
        for i in range(V):
            for j in range(V):
                if C[i][k] + C[k][j] < C[i][j]:
                    C[i][j] = C[i][k] + C[k][j]
                    Z[i][j] = Z[i][k]
        # Guardar la fotografía de este paso k
        iteraciones.append((f"Iteración k = {k + 1} (Pasando por Mundo {k + 1})", copy.deepcopy(C), copy.deepcopy(Z)))
        
    return iteraciones

def obtener_ruta_lista(Z, inicio, destino):
    if Z[inicio][destino] is None: return []
    ruta = [inicio]
    actual = inicio
    while actual != destino:
        actual = Z[actual][destino]
        if actual is None: return []
        ruta.append(actual)
    return ruta

def formatear_matriz(matriz, es_ruta=False):
    """Convierte la matriz para que se vea bien en Pandas (cambia INF por ∞ y ajusta índices a 1)"""
    df = pd.DataFrame(matriz)
    df.index = [f"M{i+1}" for i in df.index]
    df.columns = [f"M{i+1}" for i in df.columns]
    
    if es_ruta:
        # Para la matriz Z, sumamos 1 porque los nodos para el usuario empiezan en 1, no en 0
        df = df.map(lambda x: f"M{int(x)+1}" if pd.notnull(x) else "-")
    else:
        df = df.replace(INF, "∞")
    return df

# --- INTERFAZ WEB ---
st.title("🍄 Super Mario's Floyd-Warshall 🌟")
st.markdown("¡Resuelve grafos y descubre los atajos observando las iteraciones matemáticas!")

# Selección de Nivel
nivel_seleccionado = st.selectbox("🎮 SELECCIONA TU NIVEL:", list(diccionario_niveles.keys()))
grafo_actual = diccionario_niveles[nivel_seleccionado]
num_nodos = len(grafo_actual)
nombres_mundos = [f"Mundo {i+1}" for i in range(num_nodos)]

# Separador
st.markdown("---")

col_izq, col_der = st.columns([1, 2])

# Calculamos todas las iteraciones
historial_iteraciones = calcular_floyd_warshall_paso_a_paso(grafo_actual)
matriz_C_final = historial_iteraciones[-1][1]
matriz_Z_final = historial_iteraciones[-1][2]

with col_izq:
    st.header("🚩 Planear Ruta")
    
    origen = st.selectbox("📍 Inicio:", nombres_mundos, index=0)
    destino = st.selectbox("🏁 Destino:", nombres_mundos, index=num_nodos-1)
    
    idx_origen = nombres_mundos.index(origen)
    idx_destino = nombres_mundos.index(destino)
    
    ruta = obtener_ruta_lista(matriz_Z_final, idx_origen, idx_destino)
    costo = matriz_C_final[idx_origen][idx_destino]

    st.subheader("📊 Resultados")
    if costo == INF:
        st.error("¡Mamma Mia! No hay un camino posible.")
    else:
        st.metric(label="Costo Total del Viaje", value=f"{costo} Monedas 💰")
        nombres_ruta = [f"M{i+1}" for i in ruta]
        st.success(f"**Ruta óptima:** {' ➔ '.join(nombres_ruta)}")

with col_der:
    tab_mapa, tab_iteraciones = st.tabs(["🗺️ Mapa del Nivel", "🍄 Iteraciones (Paso a Paso)"])
    
    with tab_mapa:
        fig, ax = plt.subplots(figsize=(7, 5))
        G = nx.DiGraph()
        for i in range(num_nodos):
            G.add_node(i)
            for j in range(num_nodos):
                if grafo_actual[i][j] != 0 and grafo_actual[i][j] != INF:
                    G.add_edge(i, j, weight=grafo_actual[i][j])
        
        # Posicionamiento y colores de nodos estilo Mario
        pos = nx.circular_layout(G)
        # Paleta colorida para los mundos
        colores_mario = ["#E52521", "#43B047", "#5C94FC", "#FBD000", "#FF9900", "#9B59B6"]
        node_colors = [colores_mario[i % len(colores_mario)] for i in range(num_nodos)]
        
        # Dibujar nodos más pequeños (node_size=450) y con números empezando en 1
        etiquetas_nodos = {i: str(i+1) for i in range(num_nodos)}
        nx.draw_networkx_nodes(G, pos, ax=ax, node_color=node_colors, node_size=450, edgecolors="black", linewidths=1.5)
        nx.draw_networkx_labels(G, pos, ax=ax, labels=etiquetas_nodos, font_color="white", font_weight="bold", font_size=10)
        
        # Aristas base
        nx.draw_networkx_edges(G, pos, ax=ax, edge_color="gray", arrows=True, arrowsize=15, connectionstyle="arc3,rad=0.15")
        labels = nx.get_edge_attributes(G, 'weight')
        nx.draw_networkx_edge_labels(G, pos, ax=ax, edge_labels=labels, font_size=10, font_weight="bold")

        # Resaltar ruta en verde grueso
        if ruta:
            aristas_ruta = [(ruta[i], ruta[i+1]) for i in range(len(ruta)-1)]
            nx.draw_networkx_nodes(G, pos, ax=ax, nodelist=ruta, node_color="#FFFFFF", node_size=500, edgecolors="#43B047", linewidths=3)
            nx.draw_networkx_edges(G, pos, ax=ax, edgelist=aristas_ruta, edge_color="#43B047", width=3.5, arrows=True, arrowsize=20, connectionstyle="arc3,rad=0.15")

        ax.axis('off')
        st.pyplot(fig)

    with tab_iteraciones:
        st.markdown("Despliega cada iteración para ver cómo se actualizan los costos ($C$) y las rutas ($Z$).")
        
        # Crear un "acordeón" para cada iteración
        for nombre_it, mat_c, mat_z in historial_iteraciones:
            with st.expander(nombre_it, expanded=(nombre_it == historial_iteraciones[-1][0])):
                col_c, col_z = st.columns(2)
                with col_c:
                    st.markdown("**Matriz C (Costos)**")
                    st.dataframe(formatear_matriz(mat_c, es_ruta=False), use_container_width=True)
                with col_z:
                    st.markdown("**Matriz Z (Rutas)**")
                    st.dataframe(formatear_matriz(mat_z, es_ruta=True), use_container_width=True)
