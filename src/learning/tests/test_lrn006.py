from lrn006 import Estimate, compare

def test_positive():
    assert compare(Estimate("a",4,5),Estimate("b",1,2)) == "a"

def test_boundary():
    assert compare(Estimate("a",1,3),Estimate("b",2,4)) == "INSUFFICIENT_EVIDENCE"
