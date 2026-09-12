from dataclasses import dataclass, field
import re

# ----------------------------
# Normalization
# ----------------------------

def normalize_expr(expr: str) -> str:
    """
    Normaliza la expresión de entrada para facilitar el parseo.

    Convierte todos los caracteres a minúsculas excepto la 'M',
    para conservar el prefijo de mega.
    """
    return "".join(ch if ch == "M" else ch.lower() for ch in expr)


# ----------------------------
# Prefixes
# ----------------------------

PREFIXES = {
    "": 1.0,
    "k": 1e3,
    "M": 1e6,
    "m": 1e-3,
    "u": 1e-6,
    "n": 1e-9,
    "p": 1e-12,
}


# ----------------------------
# AST nodes
# ----------------------------

@dataclass
class Component:
    kind: str
    value: float
    unit: str
    nodes: list = field(default_factory=list)


@dataclass
class ParallelGroup:
    components: list
    nodes: list


@dataclass
class Circuit:
    elements: list


# ----------------------------
# Validation helpers
# ----------------------------

NODE_RE = re.compile(r"n[a-z0-9_]*$")

UNIT_MAP = {
    "v": "V",
    "e": "ohm",
    "f": "F",
    "h": "H",
}


# Reads something like:
# 10v[n0,n1]
# 5ke[n1,n2]
# 2.2Me[n2,n3]
COMPONENT_CORE_RE = re.compile(r"\s*(\d+(?:\.\d+)?)([kMmunp]?)([a-z])")


def skip_spaces(expr: str, pos: int) -> int:
    """
    Avanza la posición mientras haya espacios en blanco.
    Se usa para que el parser pueda ignorar separaciones opcionales.
    """
    while pos < len(expr) and expr[pos].isspace():
        pos += 1
    return pos


def parse_nodes(expr: str, pos: int):
    """
    Lee la lista de nodos entre corchetes.

    Ejemplo:
        [n0,n1]

    Devuelve la lista de nodos y la nueva posición de lectura.
    """
    pos = skip_spaces(expr, pos)

    if pos >= len(expr) or expr[pos] != "[":
        raise ValueError(f"Expected '[' at position {pos}")

    end = expr.find("]", pos + 1)
    if end == -1:
        raise ValueError(f"Missing closing ']' starting at position {pos}")

    raw = expr[pos + 1:end]
    nodes = [n.strip() for n in raw.split(",") if n.strip()]

    if len(nodes) != 2:
        raise ValueError(
            f"Exactly 2 nodes are required, got {len(nodes)} in [{raw}]"
        )

    for node in nodes:
        if not NODE_RE.fullmatch(node):
            raise ValueError(f"Invalid node name: {node!r}")

    return nodes, end + 1


def parse_component_core(expr: str, pos: int):
    """
    Lee la parte básica de un componente antes de los nodos.

    Ejemplos válidos:
        10v
        5ke
        2.2Me

    Convierte el valor numérico aplicando el prefijo correspondiente
    y devuelve un objeto Component parcialmente cargado.
    """
    pos = skip_spaces(expr, pos)
    m = COMPONENT_CORE_RE.match(expr, pos)
    if not m:
        raise ValueError(f"Invalid component at position {pos}: {expr[pos:pos+40]!r}")

    number = float(m.group(1))
    prefix = m.group(2)
    kind = m.group(3)

    if prefix not in PREFIXES:
        raise ValueError(f"Invalid prefix {prefix!r} at position {pos}")

    if kind not in UNIT_MAP:
        raise ValueError(f"Unsupported component kind {kind!r} at position {pos}")

    value = number * PREFIXES[prefix]
    unit = UNIT_MAP[kind]

    comp = Component(kind=kind, value=value, unit=unit)
    return comp, m.end()


def parse_single_component(expr: str, pos: int):
    """
    Parsea un componente individual con sus dos nodos.

    Ejemplo:
        10v[n0,n1]

    Devuelve el componente completo y la posición final de lectura.
    """
    comp, pos = parse_component_core(expr, pos)
    nodes, pos = parse_nodes(expr, pos)
    comp.nodes = nodes
    return comp, pos


def parse_group(expr: str, pos: int):
    """
    Parsea un grupo compacto de componentes en paralelo.

    Ejemplo:
        (5ke,10ke)[n0,n1]

    Todos los componentes dentro del grupo comparten los mismos nodos.
    """
    pos = skip_spaces(expr, pos)

    if pos >= len(expr) or expr[pos] != "(":
        raise ValueError(f"Expected '(' at position {pos}")

    pos += 1
    components = []

    while True:
        pos = skip_spaces(expr, pos)

        if pos >= len(expr):
            raise ValueError("Unclosed group: missing ')'")

        if expr[pos] == ")":
            pos += 1
            break

        comp, pos = parse_component_core(expr, pos)
        components.append(comp)

        pos = skip_spaces(expr, pos)

        if pos >= len(expr):
            raise ValueError("Unclosed group: missing ')'")

        if expr[pos] == ",":
            pos += 1
            continue

        if expr[pos] == ")":
            pos += 1
            break

        raise ValueError(
            f"Expected ',' or ')' at position {pos}, got {expr[pos]!r}"
        )

    nodes, pos = parse_nodes(expr, pos)

    for comp in components:
        comp.nodes = nodes[:]

    return ParallelGroup(components=components, nodes=nodes), pos


def parse_item(expr: str, pos: int):
    """
    Determina si el próximo elemento de la entrada es:

    - un componente individual: componente[n0,n1]
    - un grupo de componentes: (componente, componente, ...)[n0,n1]
    """
    pos = skip_spaces(expr, pos)

    if pos >= len(expr):
        return None, pos

    if expr[pos] == "(":
        return parse_group(expr, pos)

    return parse_single_component(expr, pos)


def parse_circuit(expr: str) -> Circuit:
    """
    Normaliza la expresión y construye el circuito completo.

    Recorre toda la entrada, reconoce cada elemento y lo guarda en
    un objeto Circuit.
    """
    expr = normalize_expr(expr)
    pos = 0
    elements = []

    while True:
        pos = skip_spaces(expr, pos)

        if pos >= len(expr):
            break

        item, pos = parse_item(expr, pos)
        elements.append(item)

    return Circuit(elements)


# ----------------------------
# Pretty print
# ----------------------------

def print_tree(node, indent: int = 0):
    """
    Imprime en pantalla el árbol interno del circuito con formato jerárquico.

    Sirve para depurar y visualizar cómo quedó parseada la entrada.
    """
    pad = "  " * indent

    if isinstance(node, Circuit):
        print(f"{pad}Circuit")
        for elem in node.elements:
            print_tree(elem, indent + 1)

    elif isinstance(node, ParallelGroup):
        print(f"{pad}ParallelGroup nodes={node.nodes}")
        for comp in node.components:
            print_tree(comp, indent + 1)

    elif isinstance(node, Component):
        print(
            f"{pad}Component(kind={node.kind!r}, value={node.value}, "
            f"unit={node.unit!r}, nodes={node.nodes})"
        )

    else:
        raise TypeError(f"Unknown node type: {type(node)}")
