from pathlib import PurePath

from entangled.readers.code import read_top_level, read_block
from entangled.readers import run_reader
from entangled.model import ReferenceId, ReferenceName
from entangled.errors.user import IndentationError, ParseError
from entangled.iterators import run_generator, Peekable

import pytest


hs_tgt_annotated = """
-- ~/~ begin <<fib.md#fib.hs>>[init]
-- ~/~ begin <<fib.md#fibonacci>>[init]
fibonacci :: Int -> Int -> [Int]
fibonacci a b = a : fibonacci b (a + b)
-- ~/~ end

main :: IO ()
main = putStrLn $ show $ take 20 $ fibonacci 1 1
-- ~/~ end
""".lstrip()


block0 = """
fibonacci :: Int -> Int -> [Int]
fibonacci a b = a : fibonacci b (a + b)
""".lstrip()


block1 = """
<<fibonacci>>

main :: IO ()
main = putStrLn $ show $ take 20 $ fibonacci 1 1
""".lstrip()


def test_code_reader():
    blocks, _ = run_reader(read_top_level, hs_tgt_annotated)
    assert blocks[0].reference_id == ReferenceId(ReferenceName((), "fibonacci"), PurePath("fib.md"), 0)
    assert blocks[0].content == block0
    assert blocks[1].reference_id == ReferenceId(ReferenceName((), "fib.hs"), PurePath("fib.md"), 0)
    assert blocks[1].content == block1


code2 = """
# ~/~ begin <<a.md#a.py>>[init]
only this:
    # ~/~ begin <<a.md#a>>[init]
    a1
    # ~/~ end
    # ~/~ begin <<a.md#a>>[1]
    a2
    # ~/~ end
    # ~/~ begin <<a.md#a>>[init]
    a1
    # ~/~ end
    # ~/~ begin <<a.md#a>>[1]
    a2
    # ~/~ end
# ~/~ end
""".lstrip()


code2_apy = """
only this:
    <<a>>
    <<a>>
""".lstrip()


def test_ref_twice():
    blocks, _ = run_reader(read_top_level, code2)
    assert blocks[0].reference_id == ReferenceId(ReferenceName((), "a"), PurePath("a.md"), 0)
    assert blocks[4].content == code2_apy


code3 = """
#!shebang!
# ~/~ begin <<a.md#a.py>>[init]
and this
# ~/~ end
""".lstrip()


hasshebang = """
and this
""".lstrip()


def test_header():
    blocks, _ = run_reader(read_top_level, code3)
    assert blocks[0].content == hasshebang


indent_error1 = """
    # ~/~ begin <<a.md#a.py>>[init]
This is an error
    # ~/~ end
"""

indent_error2 = """
# ~/~ begin <<a.md#a.py>>[init]
This is an error
    # ~/~ end
"""

indent_error3 = """
    # ~/~ begin <<a.md#a.py>>[init]
    This is an error
# ~/~ end
"""

indent_error4 = """
    # ~/~ begin <<a.md#a.py>>[init]
# ~/~ begin <<a.md#b>>[init]
This is an error
# ~/~ end
    # ~/~ end
"""


def test_indent_errors():
    for inp in [indent_error1, indent_error2, indent_error3, indent_error4]:
        with pytest.raises(IndentationError):
            _ = run_reader(read_top_level, inp)


def test_empty():
    assert run_generator(read_top_level(Peekable(iter([])))) == ([], None)
    assert run_generator(read_block((), "", Peekable(iter([])))) == ([], None)


eof_error = """
# ~/~ begin <<a.md#a.py>>[init]
This is an error
"""

def test_eof():
    with pytest.raises(ParseError):
        _ = run_reader(read_top_level, eof_error)
