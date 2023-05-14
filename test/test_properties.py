from entangled.properties import read_properties, Id, Class, Attribute


def test_id():
    assert read_properties("#myid") == [Id("myid")]
    assert str(Id("myid")) == "#myid"


def test_class():
    assert read_properties(".myclass") == [Class("myclass")]
    assert str(Class("myclass") == ".myclass")


def test_attribute():
    assert read_properties("key=value") == [Attribute("key", "value")]
    assert read_properties('key =   "value"') == [Attribute("key", "value")]


def test_properties():
    assert read_properties(".class #id key=value") == [
        Class("class"),
        Id("id"),
        Attribute("key", "value"),
    ]
