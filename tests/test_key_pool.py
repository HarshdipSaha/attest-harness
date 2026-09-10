import pytest
from attest_harness.providers.key_pool import KeyPool


def test_rotate_cycles_and_wraps():
    p = KeyPool(["a", "b", "c"])
    assert p.current == "a"
    assert p.rotate() == "b"
    assert p.rotate() == "c"
    assert p.rotate() == "a"  # wraps


def test_dedups_preserving_order():
    p = KeyPool(["a", "b", "a", "c", "b"])
    assert p.keys == ["a", "b", "c"]


def test_drops_empty_keys():
    p = KeyPool(["", "a", "", "b"])
    assert p.keys == ["a", "b"]


def test_empty_pool_raises():
    with pytest.raises(ValueError):
        KeyPool([])
    with pytest.raises(ValueError):
        KeyPool(["", ""])


def test_single_key_rotate_is_a_noop_cycle():
    p = KeyPool(["only"])
    assert p.current == "only"
    assert p.rotate() == "only"
    assert len(p) == 1
