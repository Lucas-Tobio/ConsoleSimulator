import numpy as np
from components import Component, ParallelGroup

def iter_components(circuit):
    """
    Aplana el circuito y devuelve una lista lineal de componentes.

    Si encuentra un ParallelGroup, extrae sus componentes internos para
    que luego puedan ser estampados uno por uno en la matriz.
    """
    flat = []

    for elem in circuit.elements:
        if isinstance(elem, Component):
            flat.append(elem)
        elif isinstance(elem, ParallelGroup):
            flat.extend(elem.components)
        else:
            raise TypeError(f"Elemento desconocido: {type(elem)}")

    return flat


def collect_nodes(components):
    """
    Recolecta todos los nodos usados por los componentes del circuito.

    Devuelve una lista ordenada de nodos únicos.
    """
    nodes = set()
    for c in components:
        for n in c.nodes:
            nodes.add(n)
    return sorted(nodes)


def build_mna_matrix(circuit, ground="n0"):
    """
    Construye la matriz MNA del circuito para resistencias y fuentes DC.

    El procedimiento consiste en:
    - identificar los nodos desconocidos,
    - asignar índices a cada nodo,
    - agregar una incógnita extra por cada fuente de tensión,
    - estampar resistencias y fuentes en la matriz,
    - devolver la matriz A y el vector z listos para resolver.
    """
    components = iter_components(circuit)
    nodes = collect_nodes(components)

    if ground not in nodes:
        raise ValueError(f"El nodo de referencia {ground!r} no existe en el circuito")

    # Nodos desconocidos = todos menos tierra
    unknown_nodes = [n for n in nodes if n != ground]
    node_index = {n: i for i, n in enumerate(unknown_nodes)}

    # Fuentes de tensión
    voltage_sources = [c for c in components if c.kind == "v"]

    n = len(unknown_nodes)
    m = len(voltage_sources)

    # Tamaño total MNA
    size = n + m

    # Matriz y vector
    A = np.zeros((size, size), dtype=float)
    z = np.zeros(size, dtype=float)

    def idx(node):
        """
        Devuelve el índice de una tensión nodal.
        Si es tierra, devuelve None.
        """
        if node == ground:
            return None
        return node_index[node]

    # ----------------------------
    # 1) Estampar resistencias
    # ----------------------------
    for c in components:
        if c.kind != "e":
            continue

        n1, n2 = c.nodes[0], c.nodes[1]
        g = 1.0 / c.value  # conductancia

        i = idx(n1)
        j = idx(n2)

        if i is not None:
            A[i, i] += g
        if j is not None:
            A[j, j] += g
        if i is not None and j is not None:
            A[i, j] -= g
            A[j, i] -= g

    # ----------------------------
    # 2) Estampar fuentes de tensión
    # ----------------------------
    # Cada fuente agrega una incógnita de corriente.
    # Su índice en la matriz es n + k
    for k, c in enumerate(voltage_sources):
        n1, n2 = c.nodes[0], c.nodes[1]
        vs_idx = n + k

        i = idx(n1)
        j = idx(n2)

        # Conexión entre nodos y corriente de la fuente
        # Columna de la fuente en las ecuaciones nodales
        if i is not None:
            A[i, vs_idx] -= 1.0
            A[vs_idx, i] -= 1.0
        if j is not None:
            A[j, vs_idx] += 1.0
            A[vs_idx, j] += 1.0

        # Ecuación de la fuente:
        # V(n1) - V(n2) = value
        z[vs_idx] = c.value

    return A, z, node_index, voltage_sources


def solve_mna(circuit, ground="n0"):
    """
    Construye y resuelve el sistema MNA del circuito.

    Devuelve el vector de solución junto con la matriz y los datos
    auxiliares necesarios para interpretar el resultado.
    """
    A, z, node_index, voltage_sources = build_mna_matrix(circuit, ground=ground)

    try:
        x = np.linalg.solve(A, z)
    except np.linalg.LinAlgError as e:
        raise ValueError(f"El sistema no se pudo resolver: {e}")

    return x, A, z, node_index, voltage_sources


def print_solution(x, node_index, voltage_sources, ground="n0"):
    """
    Muestra las tensiones nodales y las corrientes asociadas a las
    fuentes de tensión.

    Se usa después de resolver el sistema para interpretar los resultados.
    """
    inv_node_index = {idx: node for node, idx in node_index.items()}
    n = len(node_index)

    print("Tensiones nodales:")
    print(f"  {ground} = 0.0 V")

    for i in range(n):
        node = inv_node_index[i]
        print(f"  {node} = {x[i]:.6f} V")

    print("\nCorrientes por fuentes de tensión:")
    for k, src in enumerate(voltage_sources):
        current = x[n + k]
        n1, n2 = src.nodes
        print(f"  I({n1}->{n2}) = {current:.6f} A")
