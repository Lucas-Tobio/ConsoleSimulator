import unittest

from components import parse_circuit
from stamping import solve_mna


class CircuitSolverTests(unittest.TestCase):
    def solve(self, expression):
        return solve_mna(parse_circuit(expression), ground="n0")

    def test_voltage_source_uses_the_documented_polarity(self):
        x, _, _, node_index, sources = self.solve("10v[n0,n1] 10e[n1,n0]")

        self.assertEqual(len(sources), 1)
        self.assertAlmostEqual(x[node_index["n1"]], -10.0)
        self.assertAlmostEqual(x[len(node_index)], -1.0)

    def test_parallel_resistors_are_stamped_individually(self):
        x, _, _, node_index, _ = self.solve(
            "10v[n1,n0] (10e,10e)[n1,n2] 10e[n2,n0]"
        )

        self.assertAlmostEqual(x[node_index["n1"]], 10.0)
        self.assertAlmostEqual(x[node_index["n2"]], 20.0 / 3.0)

    def test_invalid_resistance_is_reported_before_stamping(self):
        with self.assertRaisesRegex(ValueError, "greater than zero"):
            parse_circuit("0e[n0,n1]")

    def test_empty_parallel_group_is_rejected(self):
        with self.assertRaisesRegex(ValueError, "at least one"):
            parse_circuit("()[n0,n1]")

    def test_unimplemented_reactive_components_are_rejected(self):
        with self.assertRaisesRegex(ValueError, "Unsupported component kind"):
            parse_circuit("1f[n0,n1]")

    def test_disconnected_resistive_subnetwork_reports_singular_mna(self):
        with self.assertRaisesRegex(ValueError, "matriz MNA singular"):
            self.solve("10e[n0,n1] 10e[n2,n3]")


if __name__ == "__main__":
    unittest.main()
