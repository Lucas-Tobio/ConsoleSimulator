# Circuit Solver

Simulador de circuitos en consola basado en nodos y análisis nodal modificado (MNA).

## Qué hace
- Parsea una netlist compacta escrita por consola.
- Reconoce resistencias, fuentes de tensión y grupos en paralelo.
- Construye la matriz MNA.
- Resuelve tensiones nodales y corrientes de fuentes.

## Sintaxis
- Fuente de tensión: `10v[n+,n-]`, donde `V(n+) - V(n-) = 10 V`.
- Resistencia: `5ke[n1,n2]`.
- Grupo en paralelo: `(5ke,10ke)[n1,n2]`.

## Convenciones
- `n0` se usa como tierra.
- `v` = fuente de tensión
- `e` = resistencia
- `M` = mega, `k` = kilo, etc.
- Una fuente puede usar un valor negativo, por ejemplo `-5v[n1,n0]`.
- La corriente de una fuente se informa de su primer nodo al segundo. Un
  valor negativo significa que la fuente entrega corriente.
- Las resistencias deben ser estrictamente mayores que cero.

## Ejemplo

`10v[n1,n0] (10e,10e)[n1,n2] 10e[n2,n0]`

Este circuito tiene una fuente de 10 V, dos resistencias de 10 ohmios en
paralelo entre `n1` y `n2` (equivalentes a 5 ohmios) y una resistencia de
10 ohmios entre `n2` y tierra. Los resultados esperados son:

```
n0 = 0 V
n1 = 10 V
n2 = 6.666667 V
I(n1->n0) = -0.666667 A
```

Por ejemplo, `10v[n0,n1]` fija `n1` en `-10 V`, porque el primer nodo de la
fuente es el terminal positivo. Esto evita ambigüedad al escribir una fuente
con tierra como primer nodo.

## Estructura del proyecto
- `components.py`: parseo y estructuras de datos
- `stamping.py`: armado y solución de la MNA
- `main.py`: interfaz por consola

## Requisitos
- Python 3.x
- NumPy

Instalación y ejecución en un entorno virtual:

```bash
python3 -m venv .venv
.venv/bin/pip install -r requirements.txt
.venv/bin/python main.py
```

Para ejecutar las pruebas:

```bash
.venv/bin/python -B -m unittest discover -v
```

Este proyecto implementa un simulador de circuitos en consola basado en nodos y análisis nodal modificado (MNA).  
Por el momento soporta resistencias y fuentes ideales de tensión DC.
