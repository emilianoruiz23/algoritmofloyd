import streamlit as st
import networkx as nx
import matplotlib.pyplot as plt
import pandas as pd
import copy
from fpdf import FPDF

# --- CONFIGURACIÓN DE LA PÁGINA ---
st.set_page_config(page_title="Mario's Star Path Finder", page_icon="🍄", layout="wide")

INF = float('inf')

# --- DEFINICIÓN DE LOS NIVELES (GRAFOS) ---
grafo_clase = [
    [0,   3, INF, INF, INF,   2],
    [INF, 0,  -1, INF, INF,   0],
    [INF, INF, 0,  -2, INF,   5],
    [INF, INF, INF, 0, INF,   5],
    [1,   INF, INF, 8,   0, INF],
    [INF, INF, INF, INF, 5,   0]
]

grafo_desierto = [
    [0,   8, INF,  1],
    [INF, 0,   1, INF],
    [4,  INF,  0, INF],
    [INF, 2,   9,  0]
]

grafo_aislamiento = [
    [0,   0,   3,  -2],
    [INF, 0,   1,  -1],
    [INF, INF, 0,   3],
    [INF, INF, INF, 0]
]

grafo_ciclo_negativo = [
    [0,   1,   INF, INF],
    [INF, 0,  -2,   INF],
    [0,   INF, 0,   2],
    [1,   INF, INF, 0]
]

diccionario_niveles = {
    "Nivel 1: Ejemplo de Clase (6 Mundos)": grafo_clase,
    "Nivel 2: Desierto Pirámide (4 Mundos)": grafo_desierto,
    "Nivel 3 (Tarea): Red con Aislamiento (4 Mundos)": grafo_aislamiento,
    "Nivel 4 (Tarea): Red con Ciclo Negativo (4 Mundos)": grafo_ciclo_negativo,
    "🛠️ Crear mi propio Nivel (Matriz Personalizada)": None
}

# --- LÓGICA DEL ALGORITMO ---
@st.cache_data 
def calcular_floyd_warshall_paso_a_paso(grafo):
    V = len(grafo)
    C = [[grafo[i][j] for j in range(V)] for i in range(V)]
    Z = [[None for _ in range(V)] for _ in range(V)]
    
    for i in range(V):
        for j in range(V):
            if i != j and grafo[i][j] != INF:
                Z[i][j] = j
                
    iteraciones = []
    iteraciones.append(("Estado Inicial", copy.deepcopy(C), copy.deepcopy(Z), -1))

    for k in range(V):
        for i in range(V):
            for j in range(V):
                if C[i][k] != INF and C[k][j] != INF:
                    if C[i][k] + C[k][j] < C[i][j]:
                        C[i][j] = C[i][k] + C[k][j]
                        Z[i][j] = Z[i][k]
        iteraciones.append((f"Iteración k = {k + 1}", copy.deepcopy(C), copy.deepcopy(Z), k))
        
    anomalias = {
        "ciclo_negativo": False,
        "nodos_aislados_iniciales": [],
        "nodos_aislados_terminales": []
    }
    
    for i in range(V):
        if C[i][i] < 0:
            anomalias["ciclo_negativo"] = True
            
        es_terminal = all(C[i][j] == INF for j in range(V) if i != j)
        if es_terminal:
            anomalias["nodos_aislados_terminales"].append(i)
            
        es_inicial = all(C[j][i] == INF for j in range(V) if i != j)
        if es_inicial:
            anomalias["nodos_aislados_iniciales"].append(i)
            
    return iteraciones, anomalias

def obtener_ruta_lista(Z, inicio, destino):
    if Z[inicio][destino] is None: return []
    ruta = [inicio]
    actual = inicio
    while actual != destino:
        actual = Z[actual][destino]
        if actual is None: return []
        ruta.append(actual)
    return ruta

# --- FUNCIONES DE ESTILO Y PDF ---
def aplicar_estilo_pivote(df, k):
    styles = pd.DataFrame('', index=df.index, columns=df.columns)
    if k != -1: 
        styles.iloc[k, :] = 'background-color: rgba(229, 37, 33, 0.2); font-weight: bold;'
        styles.iloc[:, k] = 'background-color: rgba(229, 37, 33, 0.2); font-weight: bold;'
        styles.iloc[k, k] = 'background-color: rgba(229, 37, 33, 0.5); font-weight: bold; color: white;'
    return styles

def generar_pdf(historial):
    pdf = FPDF()
    pdf.add_page()
    pdf.set_font("Courier", size=14, style='B')
    pdf.cell(200, 10, txt="Reporte: Algoritmo de Floyd-Warshall", ln=True, align='C')
    pdf.set_font("Courier", size=10)
    pdf.cell(200, 10, txt="Detalle de iteraciones paso a paso.", ln=True, align='C')
    pdf.ln(5)

    for nombre_it, mat_c, mat_z, k in historial:
        pdf.set_font("Courier", style='B', size=12)
        pdf.cell(200, 10, txt=nombre_it, ln=True)
        
        if k != -1:
            pdf.set_font("Courier", style='I', size=10)
            pdf.cell(200, 6, txt=f"-> Pivote en evaluacion: Renglon {k+1} y Columna {k+1}", ln=True)
        
        pdf.set_font("Courier", size=10)
        pdf.cell(200, 6, txt="Matriz C (Costos):", ln=True)
        for fila in mat_c:
            texto_fila = " | ".join([f"{str(val):>5}" if val != INF else "  INF" for val in fila])
            pdf.cell(200, 5, txt=f"  [ {texto_fila} ]", ln=True)
            
        pdf.ln(2)
        pdf.cell(200, 6, txt="Matriz Z (Rutas):", ln=True)
        for fila in mat_z:
            texto_fila = " | ".join([f"M{int(val)+1:>2}" if val is not None else "  -" for val in fila])
            pdf.cell(200, 5, txt=f"  [ {texto_fila} ]", ln=True)
            
        pdf.ln(5)
        pdf.cell(200, 2, txt="-"*70, ln=True)
        pdf.ln(5)
        
    return pdf.output(dest='S').encode('latin1')

def procesar_matriz_personalizada(df_editado):
    matriz = []
    for i in range(len(df_editado)):
        fila = []
        for j in range(len(df_editado.columns)):
            if i == j:
                fila.append(0.0)
                continue
                
            val = str(df_editado.iloc[i, j]).strip().upper()
            if val in ['INF', '∞', '', 'NONE', 'NAN']:
                fila.append(INF)
            else:
                try:
                    fila.append(float(val))
                except:
                    fila.append(INF)
        matriz.append(fila)
    return matriz

# --- INTERFAZ WEB ---
st.title("🍄 Super Mario's Floyd-Warshall 🌟")

nivel_seleccionado = st.selectbox("🎮 SELECCIONA TU NIVEL:", list(diccionario_niveles.keys()))

if nivel_seleccionado == "🛠️ Crear mi propio Nivel (Matriz Personalizada)":
    st.info("Escribe los pesos de las conexiones. Usa 'INF' (o deja vacío) si no hay conexión directa. La diagonal se mantendrá en 0 automáticamente.")
    num_nodos_custom = st.slider("📏 Tamaño del Mapa (Nodos):", min_value=3, max_value=10, value=4)
    
    df_default = pd.DataFrame(INF, index=[f"M{i+1}" for i in range(num_nodos_custom)], columns=[f"M{i+1}" for i in range(num_nodos_custom)])
    for i in range(num_nodos_custom):
        df_default.iloc[i, i] = 0.0
        
    # CORRECCIÓN 1: Actualizado 'use_container_width' a 'width="stretch"'
    df_usuario = st.data_editor(df_default, width="stretch")
    grafo_actual = procesar_matriz_personalizada(df_usuario)
else:
    grafo_actual = diccionario_niveles[nivel_seleccionado]

num_nodos = len(grafo_actual)
nombres_mundos = [f"Mundo {i+1}" for i in range(num_nodos)]

# --- CÁLCULO ---
historial_iteraciones, anomalias = calcular_floyd_warshall_paso_a_paso(grafo_actual)
matriz_C_final = historial_iteraciones[-1][1]
matriz_Z_final = historial_iteraciones[-1][2]

# --- PANEL DE DIAGNÓSTICO ---
st.markdown("---")
st.subheader("🩺 Diagnóstico de la Red")
red_sana = True

if anomalias["ciclo_negativo"]:
    st.error("☠️ **¡PELIGRO! Se detectó un Ciclo Negativo.** El algoritmo de Floyd no puede encontrar una ruta óptima porque el costo disminuye infinitamente dando vueltas en el ciclo. Revisa tu matriz.")
    red_sana = False
if anomalias["nodos_aislados_iniciales"]:
    nodos_ini = [f"Mundo {i+1}" for i in anomalias["nodos_aislados_iniciales"]]
    st.warning(f"⚠️ **Aislamiento Inicial:** El(Los) nodo(s) **{', '.join(nodos_ini)}** solo exportan. Todos pueden salir de ahí, pero nadie puede llegar.")
    red_sana = False
if anomalias["nodos_aislados_terminales"]:
    nodos_term = [f"Mundo {i+1}" for i in anomalias["nodos_aislados_terminales"]]
    st.warning(f"⚠️ **Aislamiento Terminal:** El(Los) nodo(s) **{', '.join(nodos_term)}** son callejones sin salida. Todos llegan ahí, pero nadie puede salir.")
    red_sana = False

if red_sana:
    st.success("✅ **Red Sana:** No se detectaron ciclos negativos ni aislamientos totales. Lista para calcular rutas.")

st.markdown("---")
col_izq, col_der = st.columns([1, 2])

with col_izq:
    st.header("🚩 Planear Ruta")
    origen = st.selectbox("📍 Inicio:", nombres_mundos, index=0)
    destino = st.selectbox("🏁 Destino:", nombres_mundos, index=num_nodos-1)
    
    idx_origen = nombres_mundos.index(origen)
    idx_destino = nombres_mundos.index(destino)
    
    ruta = obtener_ruta_lista(matriz_Z_final, idx_origen, idx_destino)
    costo = matriz_C_final[idx_origen][idx_destino]

    st.subheader("📊 Resultados")
    if anomalias["ciclo_negativo"]:
        st.error("No calculable (Ciclo Negativo en la Red)")
    elif costo == INF:
        st.error("¡No hay un camino posible entre estos dos puntos!")
    else:
        st.metric(label="Costo Total", value=f"{costo}")
        
        if len(ruta) > 1:
            st.markdown("**Desglose del viaje:**")
            for i in range(len(ruta)-1):
                nodo_a = ruta[i]
                nodo_b = ruta[i+1]
                costo_paso = grafo_actual[nodo_a][nodo_b]
                st.write(f"M{nodo_a+1} ➔ M{nodo_b+1} (Costo: {costo_paso})")
                
        st.success(f"**Ruta Final:** {' ➔ '.join([f'M{i+1}' for i in ruta])}")

    st.markdown("---")
    st.subheader("📄 Exportar Reporte")
    st.write("Descarga todas las iteraciones detalladas.")
    pdf_bytes = generar_pdf(historial_iteraciones)
    st.download_button(label="📥 Descargar Reporte PDF", data=pdf_bytes, file_name="Iteraciones_Floyd_Warshall.pdf", mime="application/pdf")

with col_der:
    tab_iteraciones, tab_mapa = st.tabs(["🍄 Iteraciones (Paso a Paso)", "🗺️ Mapa del Nivel"])
    
    with tab_iteraciones:
        st.markdown("Las celdas resaltadas en rojo indican la **fila y columna pivote ($k$)** utilizadas en esa iteración.")
        
        for nombre_it, mat_c, mat_z, k in historial_iteraciones:
            with st.expander(f"{nombre_it} " + ("(Pivote: Renglón y Col. " + str(k+1) + ")" if k!=-1 else ""), expanded=(k == num_nodos-1)):
                col_c, col_z = st.columns(2)
                
                # CORRECCIÓN 2: Convertir todo a texto (.astype(str)) para evitar el error de PyArrow
                df_c = pd.DataFrame(mat_c, index=nombres_mundos, columns=nombres_mundos).astype(str).replace(str(INF), "∞")
                
                # Para la matriz Z, iteramos convirtiendo a string sin problemas de tipos nulos
                df_z = pd.DataFrame(mat_z, index=nombres_mundos, columns=nombres_mundos)
                for col in df_z.columns:
                    df_z[col] = df_z[col].apply(lambda x: f"M{int(x)+1}" if pd.notnull(x) else "-")
                df_z = df_z.astype(str)
                
                with col_c:
                    st.markdown("**Matriz C (Costos)**")
                    st.dataframe(df_c.style.apply(aplicar_estilo_pivote, k=k, axis=None))
                with col_z:
                    st.markdown("**Matriz Z (Rutas)**")
                    st.dataframe(df_z.style.apply(aplicar_estilo_pivote, k=k, axis=None))

    with tab_mapa:
        fig, ax = plt.subplots(figsize=(7, 5))
        G = nx.DiGraph()
        for i in range(num_nodos):
            G.add_node(i)
            for j in range(num_nodos):
                if grafo_actual[i][j] != 0 and grafo_actual[i][j] != INF:
                    G.add_edge(i, j, weight=grafo_actual[i][j])
        
        pos = nx.circular_layout(G)
        colores_mario = ["#E52521", "#43B047", "#5C94FC", "#FBD000", "#FF9900", "#9B59B6", "#A569BD", "#F1C40F", "#E67E22", "#95A5A6"]
        node_colors = [colores_mario[i % len(colores_mario)] for i in range(num_nodos)]
        
        etiquetas_nodos = {i: str(i+1) for i in range(num_nodos)}
        nx.draw_networkx_nodes(G, pos, ax=ax, node_color=node_colors[:num_nodos], node_size=450, edgecolors="black", linewidths=1.5)
        nx.draw_networkx_labels(G, pos, ax=ax, labels=etiquetas_nodos, font_color="white", font_weight="bold", font_size=10)
        nx.draw_networkx_edges(G, pos, ax=ax, edge_color="gray", arrows=True, arrowsize=15, connectionstyle="arc3,rad=0.15")
        
        labels = nx.get_edge_attributes(G, 'weight')
        nx.draw_networkx_edge_labels(G, pos, ax=ax, edge_labels=labels, font_size=9)

        if ruta and not anomalias["ciclo_negativo"]:
            aristas_ruta = [(ruta[i], ruta[i+1]) for i in range(len(ruta)-1)]
            nx.draw_networkx_nodes(G, pos, ax=ax, nodelist=ruta, node_color="#FFFFFF", node_size=500, edgecolors="#43B047", linewidths=3)
            nx.draw_networkx_edges(G, pos, ax=ax, edgelist=aristas_ruta, edge_color="#43B047", width=3.5, arrows=True, arrowsize=20, connectionstyle="arc3,rad=0.15")

        ax.axis('off')
        st.pyplot(fig)
