from pathlib import Path

from entangled.io import VirtualFS, transaction
from entangled.config import ConfigUpdate, AnnotationMethod
from entangled.interface import Document


fs = VirtualFS.from_dict({
    "fib.md": """
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
""".lstrip(),


    "fib.hs": """
fibonacci :: Int -> Int -> [Int]
fibonacci a b = a : fibonacci b (a + b)

main :: IO ()
main = putStrLn $ show $ take 20 $ fibonacci 1 1
""".lstrip(),


    "fib_annot.hs": """
-- ~/~ begin <<fib.md#fib.hs>>[init]
-- ~/~ begin <<fib.md#fibonacci>>[init]
fibonacci :: Int -> Int -> [Int]
fibonacci a b = a : fibonacci b (a + b)
-- ~/~ end

main :: IO ()
main = putStrLn $ show $ take 20 $ fibonacci 1 1
-- ~/~ end
""".lstrip()})


def test_document():
    doc = Document()

    with transaction(fs=fs) as t:
        path = Path("fib.md")
        doc.load_source(t, path)
        assert doc.source_text(path)[0] == fs[path].content
        
        doc.config |= ConfigUpdate(version="2.4", annotation=AnnotationMethod.NAKED)
        fib_hs, _ = doc.target_text(Path("fib.hs"))
        assert fib_hs == fs[Path("fib.hs")].content

        doc.config |= ConfigUpdate(version="2.4", annotation=AnnotationMethod.STANDARD)
        fib_hs, _ = doc.target_text(Path("fib.hs"))
        assert fib_hs == fs[Path("fib_annot.hs")].content

