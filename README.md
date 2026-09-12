# Circuit Solver

Simulador de circuitos en consola basado en nodos y análisis nodal modificado (MNA).

## Qué hace
- Parsea una netlist compacta escrita por consola.
- Reconoce resistencias, fuentes de tensión y grupos en paralelo.
- Construye la matriz MNA.
- Resuelve tensiones nodales y corrientes de fuentes.

## Sintaxis
- Componente simple: `10v[n0,n1]`
- Resistencia: `5ke[n1,n2]`
- Grupo en paralelo: `(5ke,10ke)[n1,n2]`

## Convenciones
- `n0` se usa como tierra.
- `v` = fuente de tensión
- `e` = resistencia
- `M` = mega, `k` = kilo, etc.

## Ejemplo
`10v[n0,n1] (10e,50ke)[n1,n2]`

## Estructura del proyecto
- `components.py`: parseo y estructuras de datos
- `stamping.py`: armado y solución de la MNA
- `main.py`: interfaz por consola

## Requisitos
- Python 3.x
- NumPy

Este proyecto implementa un simulador de circuitos en consola basado en nodos y análisis nodal modificado (MNA).  
Por el momento soporta resistencias y fuentes ideales de tensión DC.
