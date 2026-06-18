# Changelog

All notable changes to this project will be documented in this file.

## 1.0.1 (2026-06-18)

* Updated dependencies to pick up upstream security fixes (including `tornado` 6.5.7, `bleach` 6.4.0., `jupyter-server` 2.20.0)

## 1.0.0 (2026-05-16)

* Initial stable release of `shapcpm` for efficient Shapley value calculation in CPM networks.
* Added `CPMNetwork` and `CPMNetworkBuilder` for constructing task graphs with durations and dependencies.
* Added `CPMTree` and `CPMTreeAsciiRenderer` for tree-based analysis and visualization.
* Added exact Shapley value computation via `CPMNetwork.get_shapley_values_exact`.
* Added Monte Carlo Shapley value approximation via `CPMNetwork.get_shapley_values_approx`.
