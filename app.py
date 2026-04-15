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
grafo_clase = [[0, 3, INF, INF, INF, 2], [INF, 0, -1, INF, INF, 0], [INF, INF, 0, -2, INF, 5], [INF, INF, INF, 0, INF, 5], [1, INF, INF, 8, 0, INF], [INF, INF, INF, INF, 5, 0]]
grafo_desierto = [[0, 8, INF, 1], [INF, 0, 1, INF], [4, INF, 0, INF], [INF, 2, 9, 0]]
grafo_aislamiento = [[0, 0, 3, -2], [INF, 0, 1, -1], [INF, INF, 0, 3], [INF, INF, INF, 0]]
grafo_ciclo_negativo = [[0, 1, INF, INF], [INF, 0, -2, INF], [0, INF, 0, 2], [1, INF, INF, 0]]

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
        
    # Diagnóstico Avanzado
    anomalias = {
        "ciclo_negativo": False, 
        "nodos_ciclo": [],
        "ruta_ciclo": [],
        "nodos_aislados_iniciales": [], 
        "nodos_aislados_terminales": []
    }
    
    for i in range(V):
        if C[i][i] < 0: 
            anomalias["ciclo_negativo"] = True
            anomalias["nodos_ciclo"].append(i)
        if all(C[i][j] == INF for j in range(V) if i != j): 
            anomalias["nodos_aislados_terminales"].append(i)
        if all(C[j][i] == INF for j in range(V) if i != j): 
            anomalias["nodos_aislados_iniciales"].append(i)
            
    # Extraer la ruta exacta del ciclo negativo usando la Matriz Z
    if anomalias["ciclo_negativo"] and len(anomalias["nodos_ciclo"]) > 0:
        nodo_raiz = anomalias["nodos_ciclo"][0]
        ruta_c = [nodo_raiz]
        actual = Z[nodo_raiz][nodo_raiz]
        # Bucle protegido para extraer el ciclo
        while actual not in ruta_c and actual is not None:
            ruta_c.append(actual)
            actual = Z[actual][nodo_raiz]
        ruta_c.append(nodo_raiz)
        ruta_c.reverse()
        anomalias["ruta_ciclo"] = ruta_c

    return iteraciones, anomalias

# EL CINTURÓN DE SEGURIDAD (Protección contra Bucle Infinito)
def obtener_ruta_lista(Z, inicio, destino):
    if Z[inicio][destino] is None: return []
    ruta = [inicio]
    actual = inicio
    visitados = {inicio} # Guardamos memoria de donde hemos estado
    
    while actual != destino:
        actual = Z[actual][destino]
        if actual is None: return []
        
        # Si la red nos manda a un lugar que ya pisamos, rompemos el bucle
        if actual in visitados:
            ruta.append(actual)
            break 
            
        visitados.add(actual)
        ruta.append(actual)
    return ruta

# --- ESTILOS Y PDF ---
def aplicar_estilo_pivote(df, k):
    styles = pd.DataFrame('', index=df.index, columns=df.columns)
    if k != -1: 
        styles.iloc[k, :] = 'background-color: rgba(229, 37, 33, 0.1);'
        styles.iloc[:, k] = 'background-color: rgba(229, 37, 33, 0.1);'
    return styles

def generar_pdf(historial, anomalias, num_islas):
    pdf = FPDF()
    pdf.add_page()
    pdf.set_font("Courier", size=12, style='B')
    pdf.cell(200, 10, txt="Reporte: Floyd-Warshall (Matrices C y Z)", ln=True, align='C')
    
    for nombre_it, mat_c, mat_z, k in historial:
        pdf.set_font("Courier", style='B', size=10); pdf.cell(200, 8, txt=nombre_it, ln=True)
        pdf.set_font("Courier", size=8); pdf.cell(200, 4, txt="Matriz C (Costos):", ln=True)
        for fila in mat_c:
            pdf.cell(200, 4, txt=" | ".join([f"{str(v):>5}" for v in fila]), ln=True)
        pdf.cell(200, 4, txt="Matriz Z (Rutas):", ln=True)
        for fila in mat_z:
            pdf.cell(200, 4, txt=" | ".join([f"M{int(v)+1:>2}" if v is not None else "  -" for v in fila]), ln=True)
        pdf.ln(4)
        
    pdf.ln(5)
    pdf.set_font("Courier", style='B', size=12)
    pdf.cell(200, 10, txt="AUDITORIA AVANZADA DE LA RED", ln=True, align='L')
    pdf.set_font("Courier", size=10)
    
    if anomalias["ciclo_negativo"]:
        pdf.cell(200, 6, txt="[X] ERROR FATAL: Ciclo Negativo Detectado.", ln=True)
        ruta_str = " -> ".join([f"M{n+1}" for n in anomalias["ruta_ciclo"]])
        pdf.cell(200, 6, txt=f"    Ruta del ciclo: {ruta_str}", ln=True)
    else:
        pdf.cell(200, 6, txt="[OK] No hay ciclos negativos.", ln=True)
        
    if anomalias["nodos_aislados_iniciales"]:
        nodos = ", ".join([f"M{i+1}" for i in anomalias["nodos_aislados_iniciales"]])
        pdf.cell(200, 6, txt=f"[!] AISLAMIENTO INICIAL (Sin Entradas): {nodos}", ln=True)
    if anomalias["nodos_aislados_terminales"]:
        nodos = ", ".join([f"M{i+1}" for i in anomalias["nodos_aislados_terminales"]])
        pdf.cell(200, 6, txt=f"[!] AISLAMIENTO TERMINAL (Callejon Sin Salida): {nodos}", ln=True)
        
    if num_islas > 1:
        pdf.cell(200, 6, txt=f"[!] FRAGMENTACION: La red esta rota en {num_islas} islas aisladas.", ln=True)
    else:
        pdf.cell(200, 6, txt="[OK] La red es un solo bloque conectado.", ln=True)
        
    return pdf.output(dest='S').encode('latin1')

def procesar_matriz_personalizada(df_editado):
    matriz = []
    for i in range(len(df_editado)):
        fila = []
        for j in range(len(df_editado.columns)):
            if i == j: fila.append(0.0); continue
            val = str(df_editado.iloc[i, j]).strip().upper()
            if val in ['INF', '∞', '', 'NONE', 'NAN']: fila.append(INF)
            else:
                try: fila.append(float(val))
                except: fila.append(INF)
        matriz.append(fila)
    return matriz

# --- INTERFAZ ---
st.title("🍄 Super Mario's Floyd-Warshall 🌟")
nivel = st.selectbox("🎮 SELECCIONA TU NIVEL:", list(diccionario_niveles.keys()))

if nivel == "🛠️ Crear mi propio Nivel (Matriz Personalizada)":
    n = st.slider("📏 Tamaño del Nivel:", 3, 10, 4)
    df_def = pd.DataFrame("INF", index=[f"M{i+1}" for i in range(n)], columns=[f"M{i+1}" for i in range(n)])
    for i in range(n): df_def.iloc[i, i] = "0"
    grafo_actual = procesar_matriz_personalizada(st.data_editor(df_def, width="stretch", key=f"editor_{n}"))
else:
    grafo_actual = diccionario_niveles[nivel]

num_nodos = len(grafo_actual)
nombres = [f"Mundo {i+1}" for i in range(num_nodos)]

G_analisis = nx.DiGraph()
for i in range(num_nodos):
    G_analisis.add_node(i)
    for j in range(num_nodos):
        if grafo_actual[i][j] != 0 and grafo_actual[i][j] != INF:
            G_analisis.add_edge(i, j)
            
islas = list(nx.weakly_connected_components(G_analisis))
num_islas = len(islas)

historial, anomalias = calcular_floyd_warshall_paso_a_paso(grafo_actual)

st.markdown("---")
col_izq, col_der = st.columns([1, 2])

with col_izq:
    st.header("🚩 Planear Ruta")
    origen = st.selectbox("📍 Inicio:", nombres, index=0)
    destino = st.selectbox("🏁 Destino:", nombres, index=len(nombres)-1)
    idx_o, idx_d = nombres.index(origen), nombres.index(destino)
    
    # LA REGLA DE ORO: Si hay ciclo negativo, ni intentamos planear la ruta
    if anomalias["ciclo_negativo"]: 
        st.error("Ruta Abortada: Existe un Ciclo Negativo en el nivel. No es posible calcular una ruta segura.")
    else:
        ruta = obtener_ruta_lista(historial[-1][2], idx_o, idx_d)
        costo = historial[-1][1][idx_o][idx_d]
        
        if costo == INF: 
            st.error("No hay puentes que conecten estos mundos.")
        else:
            st.metric("Costo Total", f"{costo}")
            st.success(f"Ruta: {' ➔ '.join([f'M{i+1}' for i in ruta])}")
    
    st.download_button("📥 Descargar Reporte y Diagnóstico PDF", generar_pdf(historial, anomalias, num_islas), "Auditoria_Floyd.pdf", "application/pdf")

    st.markdown("---")
    st.subheader("🩺 Auditoría de la Red")
    
    if anomalias["ciclo_negativo"]:
        st.error("☠️ **CICLO NEGATIVO:** Costo infinito detectado.")
        st.write(f"**Rastreo del culpable:** {' ➔ '.join([f'M{n+1}' for n in anomalias['ruta_ciclo']])}")
    else:
        st.success("✅ Sin ciclos negativos.")

    if num_islas > 1:
        st.warning(f"🏝️ **FRAGMENTACIÓN:** El mapa está roto en {num_islas} islas independientes.")
    
    if anomalias["nodos_aislados_iniciales"]:
        st.warning(f"⛔ **Nodos Intocables (Nadie llega):** {', '.join([f'M{i+1}' for i in anomalias['nodos_aislados_iniciales']])}")
    if anomalias["nodos_aislados_terminales"]:
        st.warning(f"🛑 **Callejones (Nadie sale):** {', '.join([f'M{i+1}' for i in anomalias['nodos_aislados_terminales']])}")

with col_der:
    tab_it, tab_mapa = st.tabs(["🍄 Iteraciones (C y Z)", "🗺️ Mapa Avanzado"])
    with tab_it:
        for nombre_it, mat_c, mat_z, k in historial:
            with st.expander(f"{nombre_it}", expanded=(k == len(grafo_actual)-1)):
                c1, c2 = st.columns(2)
                with c1:
                    st.write("**Matriz C (Costos)**")
                    df_c = pd.DataFrame(mat_c, index=nombres, columns=nombres).astype(str).replace(str(INF), "∞")
                    st.dataframe(df_c.style.apply(aplicar_estilo_pivote, k=k, axis=None))
                with c2:
                    st.write("**Matriz Z (Rutas)**")
                    df_z = pd.DataFrame(mat_z, index=nombres, columns=nombres)
                    for col in df_z.columns:
                        df_z[col] = df_z[col].apply(lambda x: f"M{int(x)+1}" if pd.notnull(x) else "-")
                    df_z = df_z.astype(str)
                    st.dataframe(df_z.style.apply(aplicar_estilo_pivote, k=k, axis=None))

    with tab_mapa:
        fig, ax = plt.subplots()
        pos = nx.circular_layout(G_analisis)
        
        nodos_sanos = [n for n in G_analisis.nodes() if n not in anomalias["nodos_aislados_iniciales"] and n not in anomalias["nodos_aislados_terminales"]]
        nodos_aislados = anomalias["nodos_aislados_iniciales"] + anomalias["nodos_aislados_terminales"]
        
        nx.draw_networkx_nodes(G_analisis, pos, nodelist=nodos_sanos, node_color="#43B047", node_size=500, edgecolors="black", ax=ax)
        if nodos_aislados:
            nx.draw_networkx_nodes(G_analisis, pos, nodelist=nodos_aislados, node_color="#D5D8DC", node_size=500, edgecolors="gray", alpha=0.5, ax=ax)
            
        nx.draw_networkx_labels(G_analisis, pos, labels={i: str(i+1) for i in range(num_nodos)}, font_color="white", font_weight="bold")
        
        aristas_normales = []
        aristas_ciclo = []
        
        if anomalias["ciclo_negativo"] and len(anomalias["ruta_ciclo"]) > 0:
            rc = anomalias["ruta_ciclo"]
            aristas_ciclo = [(rc[i], rc[i+1]) for i in range(len(rc)-1)]
            aristas_normales = [e for e in G_analisis.edges() if e not in aristas_ciclo]
        else:
            aristas_normales = G_analisis.edges()

        nx.draw_networkx_edges(G_analisis, pos, edgelist=aristas_normales, edge_color="gray", arrows=True, arrowsize=15, connectionstyle="arc3,rad=0.15", ax=ax)
        
        if aristas_ciclo:
            nx.draw_networkx_edges(G_analisis, pos, edgelist=aristas_ciclo, edge_color="#E52521", width=3, arrows=True, arrowsize=20, connectionstyle="arc3,rad=0.15", ax=ax)

        labels = nx.get_edge_attributes(G_analisis, 'weight')
        nx.draw_networkx_edge_labels(G_analisis, pos, edge_labels=labels, font_size=8, ax=ax)
        
        ax.axis("off")
        st.pyplot(fig)
