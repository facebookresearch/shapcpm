# Copyright (c) Meta Platforms, Inc. and affiliates.
#
# This source code is licensed under the MIT license found in the
# LICENSE file in the root directory of this source tree.

import math
from collections.abc import Iterator
from dataclasses import dataclass
from enum import IntEnum
from functools import cache
from typing import Any, TypeVar, cast

from .cpmnetwork import CPMNetwork

K = TypeVar("K")
V = TypeVar("V")


class CPMTreeNodeKind(IntEnum):
    VALUE = 0
    FORK = 1


@dataclass(slots=True)
class CPMValueNode:
    """A leaf node in the CPM tree containing a value."""

    value: int
    kind: CPMTreeNodeKind = CPMTreeNodeKind.VALUE


@dataclass(slots=True)
class CPMForkNode:
    """A fork node in the CPM tree with a key and rejected/selected children."""

    key: str
    rejected: "CPMTreeNode"
    selected: "CPMTreeNode"
    kind: CPMTreeNodeKind = CPMTreeNodeKind.FORK


CPMTreeNode = CPMForkNode | CPMValueNode
CPMPath = dict[Any, bool]  # Preserves insertion order


class CPMTree:
    """Decision tree representing all subsets of tasks in a CPM network.

    Each fork node represents a task whose presence is being toggled; the
    ``rejected`` branch corresponds to removing the task (duration set to 0)
    and the ``selected`` branch keeps it. Each leaf (value node) holds the
    critical-path duration of the resulting subnetwork.

    The tree is the data structure underlying exact Shapley value
    computation; see :meth:`calc_shap_values`.
    """

    def __init__(self, network: CPMNetwork) -> None:
        self.task_keys: list[str] = network.get_all_task_keys()
        self.root: CPMTreeNode = CPMTree._build_tree(network, set())

    def __len__(self) -> int:
        """Return the total number of nodes in the tree."""
        return self.count_nodes()

    def calc_shap_values(self) -> dict[Any, float]:
        """Return exact Shapley values for every task in the network.

        Returns:
            Mapping from task ID to Shapley value. Tasks that never appear
            as fork nodes (e.g. dominated tasks) are still present with
            value 0.0.
        """
        # Pre-fill so tasks that never appear as fork nodes (zero-duration
        # leaves, dominated tasks) still appear in the output with value 0.0.
        values: dict[Any, float] = dict.fromkeys(self.task_keys, 0.0)

        for fork_node, fork_path, fork_path_size in CPMTree._fork_nodes(
            self.root, {}, 0
        ):
            # Iterate over each value node in the rejected branch and
            # pass an empty path as it is faster to merge fork and
            # branch paths rather than maintaining long paths for value
            for (
                rejected_node,
                rejected_path,
                rejected_path_size,
            ) in CPMTree._value_nodes(fork_node.rejected, {}, 0):
                for (
                    selected_value,
                    selected_path,
                    selected_path_size,
                ) in CPMTree._value_nodes(
                    fork_node.selected, rejected_path, rejected_path_size
                ):
                    marginal = selected_value.value - rejected_node.value
                    if marginal == 0:
                        continue

                    selected_num = selected_path_size + fork_path_size
                    rejected_num = len(selected_path) + len(fork_path) - selected_num

                    w = CPMTree._calc_weight(rejected_num, selected_num)
                    values[fork_node.key] += w * marginal

        return values

    def count_nodes(self) -> int:
        """Return the total number of nodes (forks + values) in the tree."""
        return CPMTree._count_nodes(self.root)

    def count_fork_nodes(self) -> int:
        """Return the number of fork nodes in the tree."""
        return CPMTree._count_nodes(self.root, CPMTreeNodeKind.FORK)

    def count_value_nodes(self) -> int:
        """Return the number of value (leaf) nodes in the tree."""
        return CPMTree._count_nodes(self.root, CPMTreeNodeKind.VALUE)

    @staticmethod
    def _build_tree(network: CPMNetwork, visited: set[str]) -> CPMTreeNode:
        """Recursively build the CPM decision tree from the network."""
        remaining_nodes = [
            node for node in network.get_critical_path() if node not in visited
        ]

        if len(remaining_nodes) == 0:
            return CPMValueNode(value=network.get_last_end_time())

        # Pick the first node as the fork. This strategy is arbitrary, but it
        # creates trees where nodes appear in their topological order which
        # makes it easier to interpret.
        fork_key = remaining_nodes[0]

        visited.add(fork_key)

        # When node is selected we pass the network intact.
        selected = CPMTree._build_tree(network, visited)

        # When node is rejected we temporarily set the duration to 0 to act as
        # it was removed from the network.
        original_duration = network.get_task_duration(fork_key)
        network.set_task_duration(fork_key, 0)
        rejected = CPMTree._build_tree(network, visited)
        network.set_task_duration(fork_key, original_duration)

        visited.remove(fork_key)

        return CPMForkNode(key=fork_key, rejected=rejected, selected=selected)

    @staticmethod
    @cache
    def _calc_weight(r: int, s: int) -> float:
        """Shapley combinatorial weight ``r! * s! / (r + s + 1)!``.

        Computed in log-space via ``lgamma`` to avoid overflow at large
        factorials. Equivalent to ``B(r + 1, s + 1)`` but ~1.3x faster than
        ``scipy.special.beta`` and avoids the scipy dependency.
        """
        return math.exp(
            math.lgamma(r + 1) + math.lgamma(s + 1) - math.lgamma(r + s + 2)
        )

    @staticmethod
    def _fork_nodes(
        node: CPMTreeNode,
        path: CPMPath,
        path_size: int,
    ) -> Iterator[tuple[CPMForkNode, CPMPath, int]]:
        """Yield every fork node in the subtree along with its current path.

        The yielded ``path`` mapping is mutated during iteration; callers
        that need to retain it must call ``copy()`` before mutating.
        """
        if node.kind == CPMTreeNodeKind.VALUE:
            return

        node = cast(CPMForkNode, node)
        yield (node, path, path_size)
        path[node.key] = False
        yield from CPMTree._fork_nodes(node.rejected, path, path_size)
        path[node.key] = True
        yield from CPMTree._fork_nodes(node.selected, path, path_size + 1)
        del path[node.key]

    @staticmethod
    def _value_nodes(
        node: CPMTreeNode, path: CPMPath, size: int
    ) -> Iterator[tuple[CPMValueNode, CPMPath, int]]:
        """Yield value nodes reachable under the constraints in ``path``."""
        if node.kind == CPMTreeNodeKind.VALUE:
            node = cast(CPMValueNode, node)
            yield (node, path, size)
        else:
            node = cast(CPMForkNode, node)
            if node.key in path:
                if path[node.key]:
                    yield from CPMTree._value_nodes(node.selected, path, size)
                else:
                    yield from CPMTree._value_nodes(node.rejected, path, size)
            else:
                path[node.key] = False
                yield from CPMTree._value_nodes(node.rejected, path, size)
                path[node.key] = True
                yield from CPMTree._value_nodes(node.selected, path, size + 1)
                path.popitem()  # Removes last inserted key (Python 3.7+).

    @staticmethod
    def _count_nodes(node: CPMTreeNode, kind: CPMTreeNodeKind | None = None) -> int:
        """Recursively count all nodes in the tree."""
        return CPMTree._count_nodes_impl(
            node,
            1 if kind is None or kind == CPMTreeNodeKind.VALUE else 0,
            1 if kind is None or kind == CPMTreeNodeKind.FORK else 0,
        )

    @staticmethod
    def _count_nodes_impl(
        node: CPMTreeNode, value_node_val: int, fork_node_val: int
    ) -> int:
        """Recursively count all nodes in the tree."""
        if node.kind == CPMTreeNodeKind.VALUE:
            return value_node_val
        node = cast(CPMForkNode, node)
        return (
            fork_node_val
            + CPMTree._count_nodes_impl(node.rejected, value_node_val, fork_node_val)
            + CPMTree._count_nodes_impl(node.selected, value_node_val, fork_node_val)
        )


class CPMTreeAsciiRenderer:
    """Renders a CPMTree as ASCII art."""

    @staticmethod
    def render(tree: CPMTree, max_level: int = 6) -> str:
        """Render an entire ``CPMTree`` as ASCII art.

        Args:
            tree: The tree to render.
            max_level: Maximum depth to render (default: 6).

        Returns:
            A string containing the ASCII representation of the tree.
        """
        return CPMTreeAsciiRenderer.render_node(tree.root, max_level)

    @staticmethod
    def render_node(node: CPMTreeNode, max_level: int = 6) -> str:
        """Render an arbitrary subtree rooted at ``node`` as ASCII art.

        Args:
            node: The root of the subtree to render.
            max_level: Maximum depth to render (default: 6).

        Returns:
            A string containing the ASCII representation of the subtree.
        """
        lines: list[str] = []
        CPMTreeAsciiRenderer._render_node(
            node=node,
            prefix="",
            is_selected=False,
            is_root=True,
            max_level=max_level,
            current_level=0,
            lines=lines,
        )
        return "\n".join(lines)

    @staticmethod
    def _render_node(
        node: CPMTreeNode,
        prefix: str,
        is_selected: bool,
        is_root: bool,
        max_level: int,
        current_level: int,
        lines: list[str],
    ) -> None:
        if max_level is not None and current_level >= max_level:
            lines.append(prefix + ("└─✔─ ..." if is_selected else "┌─✘─ ..."))
            return

        if isinstance(node, CPMForkNode):
            CPMTreeAsciiRenderer._render_node(
                node.rejected,
                prefix=prefix + ("     " if (not is_selected or is_root) else "│    "),
                is_selected=False,
                is_root=False,
                max_level=max_level,
                current_level=current_level + 1,
                lines=lines,
            )
            if is_root:
                lines.append(prefix + "─────● " + f"Fork({node.key})")
            else:
                lines.append(
                    prefix
                    + ("└─✔──● " if is_selected else "┌─✘──● ")
                    + f"Fork({node.key})"
                )
            CPMTreeAsciiRenderer._render_node(
                node.selected,
                prefix=prefix + ("     " if (is_selected or is_root) else "│    "),
                is_selected=True,
                is_root=False,
                max_level=max_level,
                current_level=current_level + 1,
                lines=lines,
            )
        else:
            lines.append(
                prefix + ("└─✔─ " if is_selected else "┌─✘─ ") + f"Value({node.value})"
            )
