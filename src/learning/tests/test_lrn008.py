from lrn008 import audit

def test_positive():
    assert audit(8,10).learning_authorized is False

def test_boundary():
    assert audit(8,10).production_authorized is False
