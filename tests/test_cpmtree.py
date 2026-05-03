# Copyright (c) Meta Platforms, Inc. and affiliates.
#
# This source code is licensed under the MIT license found in the
# LICENSE file in the root directory of this source tree.

import math
import unittest

from shapcpm.cpmnetwork import CPMNetwork, CPMNetworkBuilder
from shapcpm.cpmtree import CPMTree


def _build_simple_network() -> CPMNetwork:
    # A(10) -> C(30)
    # B(20) -> C(30)
    # Last end time = 50
    return (
        CPMNetworkBuilder()
        .add_task("A", 10)
        .add_task("B", 20)
        .add_task("C", 30)
        .add_dependency("C", "A")
        .add_dependency("C", "B")
        .build()
    )


class CalcWeightTest(unittest.TestCase):
    def test_basic(self) -> None:
        # weight(0, 0) = 0! * 0! / 1! = 1
        self.assertAlmostEqual(CPMTree._calc_weight(0, 0), 1.0)
        # weight(1, 0) = 1! * 0! / 2! = 0.5
        self.assertAlmostEqual(CPMTree._calc_weight(1, 0), 0.5)
        # weight(1, 1) = 1! * 1! / 3! = 1/6
        self.assertAlmostEqual(CPMTree._calc_weight(1, 1), 1.0 / 6.0)

    def test_large_n_no_overflow(self) -> None:
        # 230 tasks would overflow naive f64 factorials (171! > f64::MAX).
        # Log-space computation must produce finite, positive weights.
        w = CPMTree._calc_weight(150, 79)
        self.assertTrue(math.isfinite(w), f"weight(150, 79) should be finite, got {w}")
        self.assertGreater(w, 0.0)

        w2 = CPMTree._calc_weight(229, 0)
        self.assertTrue(math.isfinite(w2), f"weight(229, 0) should be finite, got {w2}")
        self.assertGreater(w2, 0.0)


class ExactShapleyTest(unittest.TestCase):
    def test_simple_sums_to_last_end_time(self) -> None:
        net = _build_simple_network()
        shap = CPMTree(net).calc_shap_values()

        total = sum(shap.values())
        self.assertAlmostEqual(total, 50.0)
        for task, val in shap.items():
            self.assertGreaterEqual(val, 0.0, f"{task} should be non-negative")

    def test_linear_chain_equals_durations(self) -> None:
        # A(5) -> B(10) -> C(15); each task is on the critical path
        net = (
            CPMNetworkBuilder()
            .add_task("A", 5)
            .add_task("B", 10)
            .add_task("C", 15)
            .add_dependency("B", "A")
            .add_dependency("C", "B")
            .build()
        )
        shap = CPMTree(net).calc_shap_values()

        self.assertAlmostEqual(sum(shap.values()), 30.0)
        self.assertAlmostEqual(shap["A"], 5.0)
        self.assertAlmostEqual(shap["B"], 10.0)
        self.assertAlmostEqual(shap["C"], 15.0)

    def test_includes_all_tasks(self) -> None:
        # A zero-duration leaf never appears on the critical path, so the
        # decision tree never forks on it. The output must still contain it
        # with value 0.0.
        net = (
            CPMNetworkBuilder()
            .add_task("A", 10)
            .add_task("B", 20)
            .add_task("C", 30)
            .add_task("leaf", 0)
            .add_dependency("C", "A")
            .add_dependency("C", "B")
            .add_dependency("leaf", "B")
            .build()
        )
        shap = CPMTree(net).calc_shap_values()

        self.assertEqual(len(shap), 4)
        self.assertIn("leaf", shap)
        self.assertAlmostEqual(shap["leaf"], 0.0)
        self.assertAlmostEqual(sum(shap.values()), 50.0)


if __name__ == "__main__":
    unittest.main()
