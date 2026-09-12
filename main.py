import components as cps
import stamping as st


def main() -> int:
    expr = input("Enter the expression: ")

    try:
        tree = cps.parse_circuit(expr)
        x, A, z, node_index, voltage_sources = st.solve_mna(tree, ground="n0")
    except ValueError as exc:
        print(f"Error: {exc}")
        return 1

    print("\nMatriz MNA A:")
    print(A)

    print("\nVector z:")
    print(z)

    print()
    st.print_solution(x, node_index, voltage_sources, ground="n0")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
