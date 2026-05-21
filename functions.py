from dataclasses import dataclass, field
import re


# ----------------------------
# Normalization
# ----------------------------

def normalize_expr(expr: str) -> str:
    """
    Convert everything to lowercase except 'M',
    so Mega prefix is preserved.
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
    while pos < len(expr) and expr[pos].isspace():
        pos += 1
    return pos


def parse_nodes(expr: str, pos: int):
    """
    Parse a node list like: [n0,n1]
    Returns (nodes_list, new_pos)
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
    Parse the part before [nodes]:
    10v
    5ke
    2.2Me
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
    Parse:
      component[n0,n1]
    """
    comp, pos = parse_component_core(expr, pos)
    nodes, pos = parse_nodes(expr, pos)
    comp.nodes = nodes
    return comp, pos


def parse_group(expr: str, pos: int):
    """
    Parse:
      (component, component, ...)[n0,n1]

    The nodes apply to all components inside the group.
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
    Parse either:
      component[n0,n1]
    or
      (component, component, ...)[n0,n1]
    """
    pos = skip_spaces(expr, pos)

    if pos >= len(expr):
        return None, pos

    if expr[pos] == "(":
        return parse_group(expr, pos)

    return parse_single_component(expr, pos)


def parse_circuit(expr: str) -> Circuit:
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


# ----------------------------
# Example
# ----------------------------

if __name__ == "__main__":
    expr = "10uh[n0,n1]  (10e,5e)[n1,n2]"
    #expr = input("Enter the expression: ")
    tree = parse_circuit(expr)
    print_tree(tree)
