# Copyright (c) Meta Platforms, Inc. and affiliates.
#
# This source code is licensed under the MIT license found in the
# LICENSE file in the root directory of this source tree.

import unittest

from shapcpm.collections import MaxHeapDict


class MaxHeapDictTest(unittest.TestCase):
    def test_empty_maxheapdict_has_length_zero(self) -> None:
        # Setup: create an empty MaxHeapDict
        hd: MaxHeapDict[str, int] = MaxHeapDict()

        # Execute & Assert: verify length is 0
        self.assertEqual(len(hd), 0)

    def test_setitem_and_getitem(self) -> None:
        # Setup: create MaxHeapDict and add items
        hd: MaxHeapDict[str, int] = MaxHeapDict()

        # Execute: add items
        hd["a"] = 10
        hd["b"] = 5
        hd["c"] = 15

        # Assert: verify values can be retrieved
        self.assertEqual(hd["a"], 10)
        self.assertEqual(hd["b"], 5)
        self.assertEqual(hd["c"], 15)

    def test_setitem_updates_existing_key(self) -> None:
        # Setup: create MaxHeapDict with initial value
        hd: MaxHeapDict[str, int] = MaxHeapDict()
        hd["a"] = 10

        # Execute: update the value
        hd["a"] = 20

        # Assert: verify value is updated
        self.assertEqual(hd["a"], 20)
        self.assertEqual(len(hd), 1)

    def test_getitem_raises_keyerror_for_missing_key(self) -> None:
        # Setup: create empty MaxHeapDict
        hd: MaxHeapDict[str, int] = MaxHeapDict()

        # Execute & Assert: verify KeyError is raised
        with self.assertRaises(KeyError):
            _ = hd["nonexistent"]

    def test_delitem_removes_key(self) -> None:
        # Setup: create MaxHeapDict with items
        hd: MaxHeapDict[str, int] = MaxHeapDict()
        hd["a"] = 10
        hd["b"] = 5

        # Execute: delete a key
        del hd["a"]

        # Assert: verify key is removed
        self.assertNotIn("a", hd)
        self.assertIn("b", hd)
        self.assertEqual(len(hd), 1)

    def test_delitem_raises_keyerror_for_missing_key(self) -> None:
        # Setup: create empty MaxHeapDict
        hd: MaxHeapDict[str, int] = MaxHeapDict()

        # Execute & Assert: verify KeyError is raised
        with self.assertRaises(KeyError):
            del hd["nonexistent"]

    def test_contains(self) -> None:
        # Setup: create MaxHeapDict with items
        hd: MaxHeapDict[str, int] = MaxHeapDict()
        hd["a"] = 10

        # Execute & Assert: verify contains checks
        self.assertIn("a", hd)
        self.assertNotIn("b", hd)

    def test_len(self) -> None:
        # Setup: create MaxHeapDict
        hd: MaxHeapDict[str, int] = MaxHeapDict()

        # Execute & Assert: verify length after operations
        self.assertEqual(len(hd), 0)

        hd["a"] = 10
        self.assertEqual(len(hd), 1)

        hd["b"] = 5
        self.assertEqual(len(hd), 2)

        del hd["a"]
        self.assertEqual(len(hd), 1)

    def test_iter(self) -> None:
        # Setup: create MaxHeapDict with items
        hd: MaxHeapDict[str, int] = MaxHeapDict()
        hd["a"] = 10
        hd["b"] = 5
        hd["c"] = 15

        # Execute: iterate over keys
        keys = set(hd)

        # Assert: verify all keys are present
        self.assertEqual(keys, {"a", "b", "c"})

    def test_peekitem_returns_largest_value(self) -> None:
        # Setup: create MaxHeapDict with items
        hd: MaxHeapDict[str, int] = MaxHeapDict()
        hd["a"] = 10
        hd["b"] = 5
        hd["c"] = 15

        # Execute: peek at largest
        key, value = hd.peekitem()

        # Assert: verify largest is returned and not removed
        self.assertEqual(key, "c")
        self.assertEqual(value, 15)
        self.assertEqual(len(hd), 3)

    def test_peekitem_raises_keyerror_when_empty(self) -> None:
        # Setup: create empty MaxHeapDict
        hd: MaxHeapDict[str, int] = MaxHeapDict()

        # Execute & Assert: verify KeyError is raised
        with self.assertRaises(KeyError):
            hd.peekitem()

    def test_popitem_returns_and_removes_largest_value(self) -> None:
        # Setup: create MaxHeapDict with items
        hd: MaxHeapDict[str, int] = MaxHeapDict()
        hd["a"] = 10
        hd["b"] = 5
        hd["c"] = 15

        # Execute: pop largest
        key, value = hd.popitem()

        # Assert: verify largest is returned and removed
        self.assertEqual(key, "c")
        self.assertEqual(value, 15)
        self.assertEqual(len(hd), 2)
        self.assertNotIn("c", hd)

    def test_popitem_raises_keyerror_when_empty(self) -> None:
        # Setup: create empty MaxHeapDict
        hd: MaxHeapDict[str, int] = MaxHeapDict()

        # Execute & Assert: verify KeyError is raised
        with self.assertRaises(KeyError):
            hd.popitem()

    def test_popitem_multiple_times_returns_in_descending_order(self) -> None:
        # Setup: create MaxHeapDict with items
        hd: MaxHeapDict[str, int] = MaxHeapDict()
        hd["a"] = 30
        hd["b"] = 10
        hd["c"] = 20

        # Execute & Assert: pop items in descending order of values
        key1, value1 = hd.popitem()
        self.assertEqual(key1, "a")
        self.assertEqual(value1, 30)

        key2, value2 = hd.popitem()
        self.assertEqual(key2, "c")
        self.assertEqual(value2, 20)

        key3, value3 = hd.popitem()
        self.assertEqual(key3, "b")
        self.assertEqual(value3, 10)

        self.assertEqual(len(hd), 0)

    def test_update_value_affects_heap_order(self) -> None:
        # Setup: create MaxHeapDict with items
        hd: MaxHeapDict[str, int] = MaxHeapDict()
        hd["a"] = 10
        hd["b"] = 20

        # Execute: update "a" to have the largest value
        hd["a"] = 30

        # Assert: verify "a" is now the largest
        key, value = hd.peekitem()
        self.assertEqual(key, "a")
        self.assertEqual(value, 30)

    def test_delete_then_pop_skips_deleted_entries(self) -> None:
        # Setup: create MaxHeapDict where largest will be deleted
        hd: MaxHeapDict[str, int] = MaxHeapDict()
        hd["a"] = 15
        hd["b"] = 10
        hd["c"] = 5

        # Execute: delete the largest, then pop
        del hd["a"]
        key, value = hd.popitem()

        # Assert: verify deleted entry is skipped
        self.assertEqual(key, "b")
        self.assertEqual(value, 10)

    def test_peekitem_after_update_returns_new_largest(self) -> None:
        # Setup: create MaxHeapDict
        hd: MaxHeapDict[str, int] = MaxHeapDict()
        hd["a"] = 30
        hd["b"] = 20
        hd["c"] = 10

        # Execute: update "a" to be smaller than "b"
        hd["a"] = 15

        # Assert: "b" is now largest
        key, value = hd.peekitem()
        self.assertEqual(key, "b")
        self.assertEqual(value, 20)

    def test_mutablemapping_methods(self) -> None:
        # Setup: create MaxHeapDict with items
        hd: MaxHeapDict[str, int] = MaxHeapDict()
        hd["a"] = 10
        hd["b"] = 5

        # Assert: test inherited MutableMapping methods
        self.assertCountEqual(list(hd.keys()), ["a", "b"])
        self.assertCountEqual(list(hd.values()), [10, 5])
        self.assertCountEqual(list(hd.items()), [("a", 10), ("b", 5)])

    def test_get_with_default(self) -> None:
        # Setup: create MaxHeapDict with items
        hd: MaxHeapDict[str, int] = MaxHeapDict()
        hd["a"] = 10

        # Execute & Assert: test get method
        self.assertEqual(hd.get("a"), 10)
        self.assertIsNone(hd.get("nonexistent"))
        self.assertEqual(hd.get("nonexistent", 42), 42)

    def test_pop_with_default(self) -> None:
        # Setup: create MaxHeapDict with items
        hd: MaxHeapDict[str, int] = MaxHeapDict()
        hd["a"] = 10

        # Execute & Assert: pop existing key
        value = hd.pop("a")
        self.assertEqual(value, 10)
        self.assertNotIn("a", hd)

        # Execute & Assert: pop nonexistent key with default
        default_value = hd.pop("nonexistent", 42)
        self.assertEqual(default_value, 42)

    def test_clear(self) -> None:
        # Setup: create MaxHeapDict with items
        hd: MaxHeapDict[str, int] = MaxHeapDict()
        hd["a"] = 10
        hd["b"] = 5

        # Execute: clear the MaxHeapDict
        hd.clear()

        # Assert: verify it's empty
        self.assertEqual(len(hd), 0)
        self.assertNotIn("a", hd)
        self.assertNotIn("b", hd)

    def test_setdefault(self) -> None:
        # Setup: create MaxHeapDict
        hd: MaxHeapDict[str, int] = MaxHeapDict()

        # Execute & Assert: setdefault on new key
        value = hd.setdefault("a", 10)
        self.assertEqual(value, 10)
        self.assertEqual(hd["a"], 10)

        # Execute & Assert: setdefault on existing key
        value = hd.setdefault("a", 20)
        self.assertEqual(value, 10)
        self.assertEqual(hd["a"], 10)

    def test_with_integer_keys(self) -> None:
        # Setup: create MaxHeapDict with integer keys
        hd: MaxHeapDict[int, int] = MaxHeapDict()
        hd[1] = 100
        hd[2] = 50
        hd[3] = 75

        # Execute: pop largest
        key, value = hd.popitem()

        # Assert: verify correct item returned
        self.assertEqual(key, 1)
        self.assertEqual(value, 100)

    def test_with_tuple_keys(self) -> None:
        # Setup: create MaxHeapDict with tuple keys
        hd: MaxHeapDict[tuple[int, int], float] = MaxHeapDict()
        hd[(0, 0)] = 1.5
        hd[(1, 1)] = 0.5
        hd[(2, 2)] = 2.5

        # Execute: pop largest
        key, value = hd.popitem()

        # Assert: verify correct item returned
        self.assertEqual(key, (2, 2))
        self.assertEqual(value, 2.5)

    def test_repeated_updates_to_same_key(self) -> None:
        # Setup: create MaxHeapDict
        hd: MaxHeapDict[str, int] = MaxHeapDict()

        # Execute: repeatedly update the same key
        hd["a"] = 100
        hd["a"] = 50
        hd["a"] = 25
        hd["a"] = 75

        # Assert: final value is correct
        self.assertEqual(hd["a"], 75)
        self.assertEqual(len(hd), 1)

        # Assert: peekitem returns current value
        key, value = hd.peekitem()
        self.assertEqual(key, "a")
        self.assertEqual(value, 75)

    def test_single_item_operations(self) -> None:
        # Setup: create MaxHeapDict with single item
        hd: MaxHeapDict[str, int] = MaxHeapDict()
        hd["only"] = 42

        # Assert: operations work correctly
        self.assertEqual(len(hd), 1)
        self.assertEqual(hd.peekitem(), ("only", 42))

        key, value = hd.popitem()
        self.assertEqual(key, "only")
        self.assertEqual(value, 42)
        self.assertEqual(len(hd), 0)

    def test_update_decreases_value_sifts_down(self) -> None:
        # Setup: create MaxHeapDict with items
        hd: MaxHeapDict[str, int] = MaxHeapDict()
        hd["a"] = 100
        hd["b"] = 50
        hd["c"] = 25

        # Execute: decrease the max value
        hd["a"] = 10

        # Assert: "b" is now the largest
        key, value = hd.peekitem()
        self.assertEqual(key, "b")
        self.assertEqual(value, 50)

    def test_update_increases_value(self) -> None:
        # Setup: create MaxHeapDict with items
        hd: MaxHeapDict[str, int] = MaxHeapDict()
        hd["a"] = 100
        hd["b"] = 50
        hd["c"] = 25

        # Execute: increase the min value to become max
        hd["c"] = 200

        # Assert: "c" is now the largest
        key, value = hd.peekitem()
        self.assertEqual(hd.peekitem(), ("c", 200))

    def test_delete_max_element(self) -> None:
        # Setup: create MaxHeapDict with items
        hd: MaxHeapDict[str, int] = MaxHeapDict()
        hd["a"] = 100
        hd["b"] = 50
        hd["c"] = 25

        # Execute: delete the max element
        del hd["a"]

        # Assert: "b" is now the largest
        key, value = hd.peekitem()
        self.assertEqual(key, "b")
        self.assertEqual(value, 50)
        self.assertEqual(len(hd), 2)

    def test_delete_middle_element(self) -> None:
        # Setup: create MaxHeapDict with items
        hd: MaxHeapDict[str, int] = MaxHeapDict()
        hd["a"] = 100
        hd["b"] = 50
        hd["c"] = 25

        # Execute: delete a middle element
        del hd["b"]

        # Assert: max is still "a", and we have 2 elements
        key, value = hd.peekitem()
        self.assertEqual(key, "a")
        self.assertEqual(value, 100)
        self.assertEqual(len(hd), 2)

        # Assert: can still pop both elements
        hd.popitem()
        key, value = hd.popitem()
        self.assertEqual(key, "c")
        self.assertEqual(value, 25)
