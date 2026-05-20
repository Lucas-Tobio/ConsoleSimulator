from dataclasses import dataclass
import re
from typing import List, Union


# ----------------------------
# AST nodes
# ----------------------------

@dataclass
class Source:
    value: float
    unit: str = "V"

@dataclass
class Resistor:
    value: float
    unit: str = "ohm"

@dataclass
class Series:
    children: list

@dataclass
class Parallel:
    children: list


Node = Union[Source, Resistor, Series, Parallel]


# ----------------------------
# Tokenizer
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

COMPONENT_RE = re.compile(r"\d+(?:\.\d+)?[kMmunp]?[ve]")

def normalize_expr(expr: str) -> str:
    return "".join(ch if ch == "M" else ch.lower() for ch in expr)

def parse_component(token: str) -> Node:
    m = re.fullmatch(r"(\d+(?:\.\d+)?)([kMmunp]?)([ve])", token)
    if not m:
        raise ValueError(f"Invalid component token: {token}")

    number = float(m.group(1))
    prefix = m.group(2)
    suffix = m.group(3)

    value = number * PREFIXES[prefix]

    if suffix == "v":
        return Source(value=value)
    elif suffix == "e":
        return Resistor(value=value)
    else:
        raise ValueError(f"Unknown component suffix in token: {token}")


def tokenize(expr: str):
    """
    Convert the input string into tokens.
    """
    tokens = []
    i = 0

    while i < len(expr):
        ch = expr[i]

        if ch.isspace():
            i += 1
            continue

        if expr[i:i+2] == "//":
            tokens.append(("PARALLEL", "//"))
            i += 2
            continue

        if ch == '-':
            tokens.append(("SERIES", "-"))
            i += 1
            continue

        if ch == '(':
            tokens.append(("LPAREN", "("))
            i += 1
            continue

        if ch == ')':
            tokens.append(("RPAREN", ")"))
            i += 1
            continue

        m = COMPONENT_RE.match(expr, i)
        if m:
            token = m.group(0)
            tokens.append(("COMPONENT", parse_component(token)))
            i += len(token)
            continue

        raise ValueError(f"Unexpected character at position {i}: {expr[i]!r}")

    return tokens


# ----------------------------
# Parser
# ----------------------------

class Parser:
    def __init__(self, tokens):
        self.tokens = tokens
        self.pos = 0

    def current(self):
        if self.pos >= len(self.tokens):
            return None
        return self.tokens[self.pos]

    def match(self, kind):
        tok = self.current()
        if tok is not None and tok[0] == kind:
            self.pos += 1
            return tok[1]
        return None

    def expect(self, kind):
        tok = self.current()
        if tok is None:
            raise ValueError(f"Expected {kind}, but reached end of input")
        if tok[0] != kind:
            raise ValueError(f"Expected {kind}, got {tok[0]} ({tok[1]!r})")
        self.pos += 1
        return tok[1]

    def parse(self) -> Node:
        node = self.parse_series()
        if self.current() is not None:
            tok = self.current()
            raise ValueError(f"Unexpected token at end: {tok[0]} ({tok[1]!r})")
        return node

    def parse_series(self) -> Node:
        # series := parallel ('-' parallel)*
        items = [self.parse_parallel()]

        while self.match("SERIES") is not None:
            items.append(self.parse_parallel())

        if len(items) == 1:
            return items[0]
        return Series(items)

    def parse_parallel(self) -> Node:
        # parallel := factor ('//' factor)*
        items = [self.parse_factor()]

        while self.match("PARALLEL") is not None:
            items.append(self.parse_factor())

        if len(items) == 1:
            return items[0]
        return Parallel(items)

    def parse_factor(self) -> Node:
        # factor := COMPONENT | '(' expr ')'
        tok = self.current()
        if tok is None:
            raise ValueError("Unexpected end of input while parsing factor")

        kind, value = tok

        if kind == "COMPONENT":
            self.pos += 1
            return value

        if kind == "LPAREN":
            self.pos += 1
            node = self.parse_series()
            self.expect("RPAREN")
            return node

        raise ValueError(f"Expected component or '(', got {kind} ({value!r})")


def parse_circuit(expr: str) -> Node:
    expr = normalize_expr(expr)
    tokens = tokenize(expr)
    parser = Parser(tokens)
    return parser.parse()


# ----------------------------
# Pretty print
# ----------------------------

def print_tree(node: Node, indent: int = 0):
    pad = "  " * indent

    if isinstance(node, Source):
        print(f"{pad}Source({node.value} V)")
    elif isinstance(node, Resistor):
        print(f"{pad}Resistor({node.value} ohm)")
    elif isinstance(node, Series):
        print(f"{pad}Series")
        for child in node.children:
            print_tree(child, indent + 1)
    elif isinstance(node, Parallel):
        print(f"{pad}Parallel")
        for child in node.children:
            print_tree(child, indent + 1)
    else:
        raise TypeError(f"Unknown node type: {type(node)}")


# ----------------------------
# Example
# ----------------------------

if __name__ == "__main__":
	expr = "10V-(50ke//10Me)-2Me"
	print(f'Example: {expr}\n')
	#expr = input(f'Ingrese la expresión: ')
	tree = parse_circuit(expr)
	print_tree(tree)
