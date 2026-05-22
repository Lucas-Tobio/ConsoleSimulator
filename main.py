import stamping as st
import components as cps
# ----------------------------
# Example
# ----------------------------

if __name__ == "__main__":
    expr = "10V[n0,n1] 50e[n1,n2] 50e[n2,n0]"
    print(f'Entrada: {expr}\n')
    #expr = input("Enter the expression: ")
    tree = cps.parse_circuit(expr)
    print(f'{tree.elements}\n')
    #print_tree(tree)
    
    x, A, z, node_index, voltage_sources = st.solve_mna(tree, ground="n0")

    print("\nMatriz MNA A:")
    print(A)

    print("\nVector z:")
    print(z)

    print()
    st.print_solution(x, node_index, voltage_sources, ground="n0")
