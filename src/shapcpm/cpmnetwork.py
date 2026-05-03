# Copyright (c) Meta Platforms, Inc. and affiliates.
#
# This source code is licensed under the MIT license found in the
# LICENSE file in the root directory of this source tree.

import random
from collections.abc import Callable
from typing import TypeVar

import networkx as nx

from .collections import MaxHeapDict

K = TypeVar("K")
V = TypeVar("V")


class CPMNetworkBuilder:
    """Builder for constructing a CPMNetwork.

    Use this class to add tasks one at a time, then call build() to create
    a fully initialized CPMNetwork with all internal structures computed.
    """

    def __init__(self) -> None:
        self._tasks: list[tuple[str, int]] = []
        self._dependencies: list[tuple[str, str]] = []

    def add_task(self, task_id: str, duration: int) -> "CPMNetworkBuilder":
        """Add a task to the builder.

        Args:
            task_id: Unique identifier for the task.
            duration: Duration of the task.

        Returns:
            Self for method chaining.
        """
        self._tasks.append((task_id, duration))
        return self

    def add_dependency(self, task_id: str, depends_on: str) -> "CPMNetworkBuilder":
        """Record that ``task_id`` depends on ``depends_on``.

        Args:
            task_id: The task that has a dependency.
            depends_on: The task that must complete before ``task_id`` can start.

        Returns:
            Self for method chaining.
        """
        self._dependencies.append((task_id, depends_on))
        return self

    def build(self) -> "CPMNetwork":
        """Build and return a fully initialized CPMNetwork.

        Returns:
            A CPMNetwork with all internal structures initialized.
        """
        return CPMNetwork._from_tasks_and_deps(self._tasks, self._dependencies)


class CPMNetwork:
    """A directed acyclic graph representing tasks with dependencies and durations.

    This class supports efficient computation of the critical path (longest path)
    through the task graph using a MaxHeapDict to track task end times.

    Use CPMNetworkBuilder to construct a CPMNetwork.
    """

    def __init__(
        self,
        graph: nx.DiGraph,
        durations: dict[str, int],
        end_time_heapdict: MaxHeapDict[str, int],
        descendants_topological_order: dict[str, list[str]],
    ) -> None:
        self.graph = graph
        self.durations = durations
        self.end_time_heapdict = end_time_heapdict
        self.descendants_topological_order = descendants_topological_order

    @classmethod
    def _from_tasks_and_deps(
        cls,
        tasks: list[tuple[str, int]],
        dependencies: list[tuple[str, str]],
    ) -> "CPMNetwork":
        """Create a CPMNetwork from flat task and dependency lists.

        Args:
            tasks: List of (task_id, duration) tuples.
            dependencies: List of (task_id, depends_on) tuples. Edges referencing
                tasks that were never added are silently dropped.

        Returns:
            A fully initialized CPMNetwork.
        """
        graph: nx.DiGraph = nx.DiGraph()
        durations: dict[str, int] = {}
        end_time_heapdict: MaxHeapDict[str, int] = MaxHeapDict()

        for task_id, duration in tasks:
            graph.add_node(task_id)
            durations[task_id] = duration

        for task_id, depends_on in dependencies:
            if depends_on in graph and task_id in graph:
                graph.add_edge(depends_on, task_id)

        # Check for cycles before proceeding
        if not nx.is_directed_acyclic_graph(graph):
            cycles = list(nx.simple_cycles(graph))
            raise ValueError(
                f"Graph contains cycles and cannot be used for CPM: {cycles}"
            )

        # Compute end times in topological order
        for task_id in nx.topological_sort(graph):
            end_time_heapdict[task_id] = cls._compute_end_time_static(
                task_id, graph, durations, end_time_heapdict
            )

        # Precompute descendants_topological_order for all nodes
        descendants_topological_order = cls._compute_descendants_topological_order(
            graph
        )

        return cls(graph, durations, end_time_heapdict, descendants_topological_order)

    @staticmethod
    def _compute_end_time_static(
        task_id: str,
        graph: nx.DiGraph,
        durations: dict[str, int],
        end_time_heapdict: MaxHeapDict[str, int],
    ) -> int:
        """Compute the end time for a task based on its dependencies."""
        predecessors = list(graph.predecessors(task_id))
        if not predecessors:
            return durations[task_id]
        max_predecessor_end = max(end_time_heapdict[pred] for pred in predecessors)
        return max_predecessor_end + durations[task_id]

    @staticmethod
    def _compute_descendants_topological_order(
        graph: nx.DiGraph,
    ) -> dict[str, list[str]]:
        """Compute the topological order of descendants for each node."""
        result: dict[str, list[str]] = {}
        for node in graph.nodes():
            descendants = nx.descendants(graph, node)
            descendants.add(node)
            subgraph = graph.subgraph(descendants)
            result[node] = list(nx.topological_sort(subgraph))
        return result

    def set_task_duration(self, task_id: str, duration: int) -> None:
        """Update the duration of an existing task and recompute affected end times.

        Args:
            task_id: The task to update.
            duration: The new duration.
        """
        if task_id not in self.graph:
            raise KeyError(f"Task {task_id} not found in graph")

        self.durations[task_id] = duration
        self._update_end_times_from(task_id)

    def get_task_duration(self, task_id: str) -> int:
        """Return the duration of an existing task."""
        return self.durations[task_id]

    def get_all_task_keys(self) -> list[str]:
        """Return all task IDs in builder insertion order."""
        return list(self.durations.keys())

    def get_task_end_time(self, task_id: str) -> int:
        """Return the end time of an existing task."""
        return self.end_time_heapdict[task_id]

    def get_last_end_time(self) -> int:
        """Return total duration of the critical path (longest path in the graph)."""
        if not self.end_time_heapdict:
            return 0
        return self.end_time_heapdict.peekitem()[1]

    def get_critical_path(self) -> list[str]:
        """Return the critical path (longest path) through the task graph.

        The critical path is the sequence of tasks that determines the minimum
        time needed to complete all tasks. Each task on the critical path starts
        immediately after its predecessor finishes.

        Returns:
            A list of task IDs representing the critical path, ordered from
            the first task to the last task.
        """
        if not self.end_time_heapdict:
            return []

        # Start from the task with the maximum end time
        current_task = self.end_time_heapdict.peekitem()[0]
        critical_path: list[str] = [current_task]

        # Trace back through predecessors, always picking the one with max end time
        while True:
            predecessors = list(self.graph.predecessors(current_task))
            if not predecessors:
                break

            # Find the predecessor with the maximum end time
            max_pred = max(predecessors, key=lambda p: self.end_time_heapdict[p])
            critical_path.append(max_pred)
            current_task = max_pred

        # Reverse to get the path from start to end
        critical_path.reverse()
        return critical_path

    def _compute_end_time(self, task_id: str) -> int:
        """Compute the end time for a task based on its dependencies."""
        predecessors = list(self.graph.predecessors(task_id))
        if not predecessors:
            return self.durations[task_id]
        max_predecessor_end = max(self.end_time_heapdict[pred] for pred in predecessors)
        return max_predecessor_end + self.durations[task_id]

    def _update_end_times_from(self, task_id: str) -> None:
        """Update end times for a task and all its descendants in topological order."""
        # Use precomputed topological order of descendants
        for node in self.descendants_topological_order[task_id]:
            self.end_time_heapdict[node] = self._compute_end_time(node)

    def copy(self) -> "CPMNetwork":
        """Create a copy of this CPMNetwork.

        Returns:
            A new CPMNetwork instance.
        """
        return CPMNetwork(
            # Graph structure is immutable so we can share it.
            graph=self.graph,
            descendants_topological_order=self.descendants_topological_order,
            # Duration and end time are mutable, so we need to deep copy them.
            durations=self.durations.copy(),
            end_time_heapdict=self.end_time_heapdict.copy(),
        )

    def get_shapley_values_exact(self) -> dict[str, float]:
        """Calculate exact Shapley values using CPMTree data structure.

        Builds a :class:`~shapcpm.cpmtree.CPMTree` from this network and
        evaluates Shapley values exactly. Suitable for networks small enough
        that the tree fits in memory; for larger networks use
        :meth:`get_shapley_values_approx`.

        Returns:
            Dictionary mapping task IDs to their Shapley values.
        """
        from .cpmtree import CPMTree

        return CPMTree(self).calc_shap_values()

    def get_shapley_values_approx(
        self,
        num_samples: int = 1000,
        progress_callback: Callable[[int], None] | None = None,
    ) -> dict[str, float]:
        """Approximate Shapley values via Monte Carlo simulation.

        Args:
            num_samples: Number of Monte Carlo samples to use.
            progress_callback: Optional callback function that receives
                current_iteration after each iteration.

        Returns:
            Dictionary mapping task IDs to their Shapley values.
        """
        task_id_list = list(self.durations.keys())
        shapley_values = dict.fromkeys(task_id_list, 0.0)

        for i in range(num_samples):
            permutation = random.sample(task_id_list, len(task_id_list))
            task_graph_copy = self.copy()
            prev_value = task_graph_copy.get_last_end_time()

            for task_id in permutation:
                task_graph_copy.set_task_duration(task_id, 0)
                curr_value = task_graph_copy.get_last_end_time()
                shapley_values[task_id] += prev_value - curr_value
                prev_value = curr_value

            if progress_callback is not None:
                progress_callback(i)

        return {key: value / num_samples for key, value in shapley_values.items()}
