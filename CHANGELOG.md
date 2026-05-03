# Changelog

All notable changes to this project will be documented in this file.

## 1.0.0 (May 16, 2026)

* Initial stable release of `shapcpm` for efficient Shapley value calculation in CPM networks.
* Added `CPMNetwork` and `CPMNetworkBuilder` for constructing task graphs with durations and dependencies.
* Added `CPMTree` and `CPMTreeAsciiRenderer` for tree-based analysis and visualization.
* Added exact Shapley value computation via `CPMNetwork.get_shapley_values_exact`.
* Added Monte Carlo Shapley value approximation via `CPMNetwork.get_shapley_values_approx`.
