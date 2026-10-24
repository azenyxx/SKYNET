from lrn001 import Experience, assess

def test_positive():
    assert assess(Experience("x", "success", True)) == "ELIGIBLE_FOR_EVALUATION"

def test_boundary():
    assert assess(Experience("x", "failure", False)) == "REQUIRES_VERIFICATION"
