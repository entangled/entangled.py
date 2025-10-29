from entangled.readers.builder import Builder


def make_sum(x):
    s = 0
    for y in x:
        s += y
        yield y
    return s


def test_builer():
    b = Builder(make_sum(range(10)))
    assert list(b) == list(range(10))
    assert b.result == sum(range(10))
