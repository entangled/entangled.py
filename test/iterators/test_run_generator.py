from entangled.iterators import run_generator


def g():
    yield 1
    yield 2
    return 3


def h():
    return 1
    yield 0


def test_run_generator():
    assert run_generator(g()) == ([1, 2], 3)
    assert run_generator(h()) == ([], 1)

