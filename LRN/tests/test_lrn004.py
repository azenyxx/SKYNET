from lrn004 import retention_gate

def test_positive():
    assert retention_gate(0.9,0.7) == "REGRESSION_DETECTED"

def test_boundary():
    assert retention_gate(None,0.7) == "INSUFFICIENT_EVIDENCE"
