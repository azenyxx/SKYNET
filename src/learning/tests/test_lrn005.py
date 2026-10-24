from lrn005 import compatibility

def test_positive():
    assert compatibility(frozenset({"a","b"}),frozenset({"a"})) == "COMPATIBLE_FOR_EVALUATION"

def test_boundary():
    assert compatibility(frozenset({"a"}),frozenset({"b"})) == "INCOMPATIBLE"
