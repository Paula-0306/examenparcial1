import sqlite3
import heapq
import networkx as nx
import matplotlib.pyplot as plt


# 1. Cargar datos desde SQLite

def cargar_datos(db_path=None, connection=None):
    close_conn = False
    if connection is None:
        if db_path is None:
            raise ValueError("Debe pasar db_path o connection")
        connection = sqlite3.connect(db_path)
        close_conn = True

    cur = connection.cursor()
    cur.execute("SELECT origen, destino, distancia FROM rutas")
    rutas = cur.fetchall()

    cur.execute("SELECT id_envio, origen, destino FROM envios")
    envios = cur.fetchall()

    cur.execute("SELECT id, nombre, ciudad FROM almacenes")
    almacenes = cur.fetchall()

    if close_conn:
        connection.close()

    return rutas, envios, almacenes



# 2. Construcción del grafo dirigido ponderado

def construir_grafo(rutas, mostrar=False):
    """
    Construye un grafo dirigido ponderado (diccionario y networkx).
    También puede imprimirlo si mostrar=True.
    """
    grafo = {}
    G = nx.DiGraph()
    nodos = set()

    for origen, destino, distancia in rutas:
        nodos.add(origen)
        nodos.add(destino)
        grafo.setdefault(origen, {})[destino] = distancia
        G.add_edge(origen, destino, weight=distancia)

    for n in nodos:
        grafo.setdefault(n, {})

    if mostrar:
        print("=== Grafo dirigido ponderado (diccionario) ===")
        for o, destinos in grafo.items():
            for d, w in destinos.items():
                print(f"{o} -> {d} : {w}")

    return grafo, G



# 3. Dijkstra sin usar NetworkX

def Dijkstra(grafo, origen):
    dist = {n: float('inf') for n in grafo}
    prev = {n: None for n in grafo}
    if origen not in grafo:
        return dist, prev

    dist[origen] = 0
    heap = [(0, origen)]
    while heap:
        d_u, u = heapq.heappop(heap)
        if d_u > dist[u]:
            continue
        for v, peso in grafo[u].items():
            alt = d_u + peso
            if alt < dist[v]:
                dist[v] = alt
                prev[v] = u
                heapq.heappush(heap, (alt, v))
    return dist, prev



# 4. Reconstrucción de camino

def reconstruir_camino(prev, origen, destino):
    camino = []
    u = destino
    if u not in prev:
        return []
    while u is not None:
        camino.insert(0, u)
        if u == origen:
            break
        u = prev[u]
    if camino and camino[0] == origen:
        return camino
    return []



# 5. Procesar envíos y mostrar resultados

def procesar_envios(grafo, envios, G=None):
    resultados = []
    for id_envio, origen, destino in envios:
        dist, prev = Dijkstra(grafo, origen)
        if origen not in grafo:
            msg = f"Envío {id_envio}: origen={origen}, destino={destino} → Ruta no encontrada (origen desconocido)"
            print(msg)
            resultados.append((id_envio, origen, destino, None, None, msg))
            continue

        if destino not in dist or dist[destino] == float('inf'):
            msg = f"Envío {id_envio}: origen={origen}, destino={destino} → Ruta no encontrada"
            print(msg)
            resultados.append((id_envio, origen, destino, None, None, msg))
        else:
            camino = reconstruir_camino(prev, origen, destino)
            msg = (f"Envío {id_envio}: origen={origen}, destino={destino}, "
                   f"distancia_mínima={dist[destino]}, ruta={' -> '.join(camino)}")
            print(msg)
            resultados.append((id_envio, origen, destino, dist[destino], camino, msg))

            # (6) Mostrar grafo destacando la ruta más corta
            if G is not None:
                mostrar_grafo(G, camino)
    return resultados



# 6. (Opcional) Representar gráficamente el grafo

def mostrar_grafo(G, ruta_destacada=None):
    """
    Dibuja el grafo con los pesos de las aristas.
    Si se pasa una ruta, la resalta en color rojo.
    """
    pos = nx.spring_layout(G, seed=42)
    labels = nx.get_edge_attributes(G, 'weight')

    plt.figure(figsize=(7, 5))
    nx.draw(G, pos, with_labels=True, node_size=1800,
            node_color="lightblue", font_weight="bold", arrowsize=20)
    nx.draw_networkx_edge_labels(G, pos, edge_labels=labels)

    if ruta_destacada and len(ruta_destacada) > 1:
        edges = list(zip(ruta_destacada, ruta_destacada[1:]))
        nx.draw_networkx_edges(G, pos, edgelist=edges, edge_color="red", width=3)

    plt.title("Grafo de rutas (en rojo: ruta más corta)")
    plt.show()



# Programa principal (ejemplo)

if __name__ == "__main__":
    # Crear base en memoria para probar 
    conn = sqlite3.connect(":memory:")
    cur = conn.cursor()
    cur.executescript("""
    CREATE TABLE almacenes(id INTEGER PRIMARY KEY, nombre TEXT, ciudad TEXT);
    CREATE TABLE rutas(origen TEXT, destino TEXT, distancia REAL);
    CREATE TABLE envios(id_envio INTEGER PRIMARY KEY, origen TEXT, destino TEXT);

    INSERT INTO almacenes VALUES
     (1,'A','Madrid'), (2,'B','Barcelona'), (3,'C','Valencia'), (4,'D','Sevilla');

    INSERT INTO rutas VALUES
     ('A','B',5.0), ('A','C',10.0), ('B','C',3.0), ('C','D',1.5), ('B','D',9.0);

    INSERT INTO envios VALUES
     (1,'A','D'), (2,'B','A'), (3,'A','C');
    """)
    conn.commit()

    rutas, envios, almacenes = cargar_datos(connection=conn)
    grafo, G = construir_grafo(rutas, mostrar=True)

    print("\n=== RESULTADOS DE LOS ENVÍOS ===")
    procesar_envios(grafo, envios, G)

    conn.close()
