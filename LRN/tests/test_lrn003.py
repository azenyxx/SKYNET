from lrn003 import Strategy, propose

def test_positive():
    assert propose((Strategy("a",5,True),Strategy("b",2,True))) == "b"

def test_boundary():
    assert propose((Strategy("a",1,False),)) == "NOT_QUALIFIED"
