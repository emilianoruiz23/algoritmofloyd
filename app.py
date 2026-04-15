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

def generar_pdf(historial, anomalias):
    pdf = FPDF()
    pdf.add_page()
    pdf.set_font("Courier", size=14, style='B')
    pdf.cell(200, 10, txt="Reporte: Algoritmo de Floyd-Warshall", ln=True, align='C')
    pdf.set_font("Courier", size=10)
    pdf.cell(200, 10, txt="Detalle de iteraciones paso a paso.", ln=True, align='C')
    pdf.ln(5)

    # Iteraciones de matrices
    for nombre_it, mat_c, mat_z, k in historial:
        pdf.set_font("Courier", style='B', size=11)
        pdf.cell(200, 8, txt=nombre_it, ln=True)
        
        if k != -1:
            pdf.set_font("Courier", style='I', size=9)
            pdf.cell(200, 5, txt=f"-> Pivote en evaluacion: Renglon {k+1} y Columna {k+1}", ln=True)
        
        pdf.set_font("Courier", size=9)
        pdf.cell(200, 5, txt="Matriz C (Costos):", ln=True)
        for fila in mat_c:
            texto_fila = " | ".join([f"{str(val):>5}" if val != INF else "  INF" for val in fila])
            pdf.cell(200, 4, txt=f"  [ {texto_fila} ]", ln=True)
            
        pdf.ln(3)
        
    # --- SECCIÓN NUEVA: DIAGNÓSTICO FINAL EN PDF ---
    pdf.ln(5)
    pdf.set_font("Courier", style='B', size=12)
    pdf.cell(200, 10, txt="DIAGNOSTICO FINAL DE LA RED", ln=True, align='L')
    pdf.set_font("Courier", size=10)
    
    red_limpia = True
    if anomalias["ciclo_negativo"]:
        pdf.cell(200, 6, txt="- ALERTA: Se detecto un Ciclo Negativo en la red.", ln=True)
        red_limpia = False
    if anomalias["nodos_aislados_iniciales"]:
        nodos = ", ".join([str(i+1) for i in anomalias["nodos_aislados_iniciales"]])
        pdf.cell(200, 6, txt=f"- AISLAMIENTO INICIAL: Nodo(s) {nodos} (Sin entradas).", ln=True)
        red_limpia = False
    if anomalias["nodos_aislados_terminales"]:
        nodos = ", ".join([str(i+1) for i in anomalias["nodos_aislados_terminales"]])
        pdf.cell(200, 6, txt=f"- AISLAMIENTO TERMINAL: Nodo(s) {nodos} (Sin salidas).", ln=True)
        red_limpia = False
    
    if red_limpia:
        pdf.cell(200, 6, txt="- RED SANA: No se encontraron anomalias estructurales.", ln=True)
        
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
    df_default = pd.DataFrame("INF", index=[f"M{i+1}" for i in range(num_nodos_custom)], columns=[f"M{i+1}" for i in range(num_nodos_custom)])
    for i in range(num_nodos_custom):
        df_default.iloc[i, i] = "0"
    df_usuario = st.data_editor(df_default, width="stretch", key=f"matriz_editor_{num_nodos_custom}")
    grafo_actual = procesar_matriz_personalizada(df_usuario)
else:
    grafo_actual = diccionario_niveles[nivel_seleccionado]

num_nodos = len(grafo_actual)
nombres_mundos = [f"Mundo {i+1}" for i in range(num_nodos)]

# --- CÁLCULO ---
historial_iteraciones, anomalias = calcular_floyd_warshall_paso_a_paso(grafo_actual)
matriz_C_final = historial_iteraciones[-1][1]
matriz_Z_final = historial_iteraciones[-1][2]

# --- VISTA PRINCIPAL ---
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
        st.error("No calculable (Ciclo Negativo)")
    elif costo == INF:
        st.error("¡No hay un camino posible!")
    else:
        st.metric(label="Costo Total", value=f"{costo}")
        if len(ruta) > 1:
            st.markdown("**Desglose:**")
            for i in range(len(ruta)-1):
                st.write(f"M{ruta[i]+1} ➔ M{ruta[i+1]+1} (Costo: {grafo_actual[ruta[i]][ruta[i+1]]})")
        st.success(f"**Ruta:** {' ➔ '.join([f'M{i+1}' for i in ruta])}")

    st.markdown("---")
    st.subheader("📄 Exportar Reporte")
    # AHORA PASAMOS AMBOS ARGUMENTOS
    pdf_bytes = generar_pdf(historial_iteraciones, anomalias)
    st.download_button(label="📥 Descargar Reporte PDF", data=pdf_bytes, file_name="Reporte_Floyd_Warshall.pdf", mime="application/pdf")

with col_der:
    tab_iteraciones, tab_mapa = st.tabs(["🍄 Iteraciones", "🗺️ Mapa"])
    with tab_iteraciones:
        for nombre_it, mat_c, mat_z, k in historial_iteraciones:
            with st.expander(f"{nombre_it}", expanded=(k == num_nodos-1)):
                df_c = pd.DataFrame(mat_c, index=nombres_mundos, columns=nombres_mundos).astype(str).replace(str(INF), "∞")
                st.dataframe(df_c.style.apply(aplicar_estilo_pivote, k=k, axis=None))

    with tab_mapa:
        fig, ax = plt.subplots(figsize=(7, 5))
        G = nx.DiGraph()
        for i in range(num_nodos):
            for j in range(num_nodos):
                if grafo_actual[i][j] != 0 and grafo_actual[i][j] != INF:
                    G.add_edge(i, j, weight=grafo_actual[i][j])
        pos = nx.circular_layout(G)
        nx.draw(G, pos, with_labels=True, node_color="#E52521", font_color="white", font_weight="bold", ax=ax, connectionstyle="arc3,rad=0.1")
        st.pyplot(fig)

# --- DIAGNÓSTICO AL FINAL ---
st.markdown("---")
st.subheader("🩺 Diagnóstico Final de la Red")
if anomalias["ciclo_negativo"]:
    st.error("☠️ Ciclo Negativo Detectado.")
elif not anomalias["nodos_aislados_iniciales"] and not anomalias["nodos_aislados_terminales"]:
    st.success("✅ Red Sana.")
else:
    st.warning("⚠️ Se detectaron aislamientos.")
