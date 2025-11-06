from functools import partial
from pathlib import PurePath

from entangled.config import Config, ConfigUpdate, AnnotationMethod
from entangled.model import Document, ReferenceMap
from entangled.readers import markdown, run_reader


md_source = """
---
entangled:
    version: "2.4"
    style: basic
    annotation: naked
---

This is a basic example of an Entangled document. We'll compute Fibonacci numbers
in Haskell!

```haskell
-- | id: fibonacci
fibonacci :: Int -> Int -> [Int]
fibonacci a b = a : fibonacci b (a + b)
```

The ability to write lazy expressions like these is unparalelled in other languages.

```haskell
-- | file: fib.hs
<<fibonacci>>

main :: IO ()
main = putStrLn $ show $ take 20 $ fibonacci 1 1
```

Enjoy!
""".lstrip()


hs_tgt = """
fibonacci :: Int -> Int -> [Int]
fibonacci a b = a : fibonacci b (a + b)

main :: IO ()
main = putStrLn $ show $ take 20 $ fibonacci 1 1
""".lstrip()


hs_tgt_annotated = """
-- ~/~ begin <<fib.md#fib.hs>>[0]
-- ~/~ begin <<fib.md#fibonacci>>[0]
fibonacci :: Int -> Int -> [Int]
fibonacci a b = a : fibonacci b (a + b)
-- ~/~ end

main :: IO ()
main = putStrLn $ show $ take 20 $ fibonacci 1 1
-- ~/~ end
""".lstrip()


def test_document():
    refs = ReferenceMap()
    path = PurePath("fib.md")
    content, config = run_reader(partial(markdown, Config(), refs), md_source, path.as_posix())

    doc = Document(config, refs, { path: content })
    assert doc.source_text(path) == md_source
    
    fib_hs, _ = doc.target_text(PurePath("fib.hs"))
    assert fib_hs == hs_tgt

    doc.config |= ConfigUpdate(version="2.4", annotation=AnnotationMethod.STANDARD)
    fib_hs, _ = doc.target_text(PurePath("fib.hs"))
    assert fib_hs == hs_tgt_annotated

