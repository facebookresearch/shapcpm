# Copyright (c) Meta Platforms, Inc. and affiliates.
#
# This source code is licensed under the MIT license found in the
# LICENSE file in the root directory of this source tree.

from collections.abc import Iterator, MutableMapping
from typing import Generic, TypeVar

K = TypeVar("K")
V = TypeVar("V")


class MaxHeapDict(MutableMapping[K, V], Generic[K, V]):
    """A dictionary that also maintains a max-heap structure based on values.

    This data structure combines the O(1) key lookup of a dictionary with
    O(1) maximal item lookup, and O(log n) mutation operations of a max-heap.
    """

    def __init__(self) -> None:
        self._pos_map: dict[K, int] = {}
        self._heap: list[tuple[V, K]] = []

    def _siftdown_max(self, startpos: int, pos: int) -> None:
        """Move item at pos up toward startpos if it's larger than its parent"""
        heap = self._heap
        newitem = heap[pos]
        while pos > startpos:
            parentpos = (pos - 1) >> 1
            parent = heap[parentpos]
            if parent < newitem:
                heap[pos] = parent
                self._pos_map[parent[1]] = pos
                pos = parentpos
                continue
            break
        heap[pos] = newitem
        self._pos_map[newitem[1]] = pos

    def _siftup_max(self, pos: int) -> None:
        """Move item at pos down toward leaves if it's smaller than its children."""
        heap = self._heap
        endpos = len(heap)
        startpos = pos
        newitem = heap[pos]
        childpos = 2 * pos + 1
        while childpos < endpos:
            selectedpos = childpos + 1
            if selectedpos < endpos and not heap[selectedpos] < heap[childpos]:
                childpos = selectedpos
            heap[pos] = heap[childpos]
            self._pos_map[heap[childpos][1]] = pos
            pos = childpos
            childpos = 2 * pos + 1
        heap[pos] = newitem
        self._pos_map[newitem[1]] = pos
        self._siftdown_max(startpos, pos)

    def __setitem__(self, key: K, value: V) -> None:
        """Set key to value, updating the heap accordingly."""
        if key in self._pos_map:
            pos = self._pos_map[key]
            old_value = self._heap[pos][0]
            self._heap[pos] = (value, key)
            # pyre-ignore[58]: V is expected to be comparable for heap operations
            if value > old_value:
                self._siftdown_max(0, pos)
            else:
                self._siftup_max(pos)
        else:
            pos = len(self._heap)
            self._heap.append((value, key))
            self._pos_map[key] = pos
            self._siftdown_max(0, pos)

    def __getitem__(self, key: K) -> V:
        """Get the value for key, raising KeyError if not found."""
        if key not in self._pos_map:
            raise KeyError(key)
        pos = self._pos_map[key]
        return self._heap[pos][0]

    def __delitem__(self, key: K) -> None:
        """Remove key from the MaxHeapDict, raising KeyError if not found."""
        if key not in self._pos_map:
            raise KeyError(key)
        pos = self._pos_map[key]
        del self._pos_map[key]

        if pos < len(self._heap) - 1:
            last_item = self._heap[-1]
            self._heap[pos] = last_item
            self._pos_map[last_item[1]] = pos
            self._heap.pop()
            if pos > 0 and self._heap[(pos - 1) >> 1] < self._heap[pos]:
                self._siftdown_max(0, pos)
            else:
                self._siftup_max(pos)
        else:
            self._heap.pop()

    def __iter__(self) -> Iterator[K]:
        """Iterate over the keys in the HeapDict."""
        return iter(self._pos_map)

    def __len__(self) -> int:
        """Return the number of items in the HeapDict."""
        return len(self._pos_map)

    def __contains__(self, key: K) -> bool:
        """Return True if key is in the HeapDict."""
        return key in self._pos_map

    def peekitem(self) -> tuple[K, V]:
        """Return the (key, value) pair with the largest value without removing it.

        Raises KeyError if the HeapDict is empty.
        """
        if not self._heap:
            raise KeyError("HeapDict is empty")
        value, key = self._heap[0]
        return (key, value)

    def popitem(self) -> tuple[K, V]:
        """Remove and return the (key, value) pair with the largest value.

        Raises KeyError if the HeapDict is empty.
        """
        if not self._heap:
            raise KeyError("HeapDict is empty")
        value, key = self._heap[0]
        del self[key]  # Use __delitem__ to properly maintain invariants
        return (key, value)

    def copy(self) -> "MaxHeapDict[K, V]":
        """Create a copy of this MaxHeapDict."""
        new_instance: MaxHeapDict[K, V] = MaxHeapDict()
        new_instance._pos_map = self._pos_map.copy()
        new_instance._heap = self._heap.copy()
        return new_instance
