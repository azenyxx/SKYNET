from lrn002 import ReplayItem, select

def test_positive():
    assert [x.identifier for x in select((ReplayItem("b",2,False),ReplayItem("a",1,True)),2)] == ["a","b"]

def test_boundary():
    assert select((ReplayItem("a",1,False),),0) == ()
