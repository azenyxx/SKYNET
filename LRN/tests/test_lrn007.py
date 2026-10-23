from lrn007 import validate

def test_positive():
    assert validate(True,True,False) == "QUALIFIED_FOR_FURTHER_VALIDATION"

def test_boundary():
    assert validate(False,True,False) == "REQUIRES_INDEPENDENT_EVIDENCE"
