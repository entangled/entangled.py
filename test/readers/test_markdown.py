from pathlib import PurePath
from entangled.document import PlainText
from entangled.readers.markdown import ignore_block
from entangled.readers.lines import numbered_lines
from entangled.config import Config
from entangled.readers.types import run_generator


test0 = """
abcdefg
"""

test1 = """
~~~markdown
``` {.python}
# this code block is ignored
```
~~~
""".strip()

def test_ignore_block():
    rv, ol = run_generator(ignore_block(Config())(numbered_lines(PurePath("-"), test1)))
    assert ol
    assert rv == [PlainText(test1)]
