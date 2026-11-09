from pathlib import Path
from contextlib import chdir

from entangled.commands import main
from entangled.interface import Context
from entangled.weave import filters, transform_markdown

import pytest


md_in = """# Example

``` {.python file=hello.py}
<<main>>
```

``` {.python #main .extra}
print("hello")
```

``` {.python}
anonymous = True
```
"""


def weave(text: str, *names: str) -> str:
    return "".join(transform_markdown(Context(), text, *(filters[n] for n in names)))


def test_identity():
    assert weave(md_in) == md_in


def test_title():
    out = weave(md_in, "title")
    assert '```python {title="file: hello.py"}\n' in out
    assert '```python {#main .extra title="#main"}\n' in out
    assert "```python\nanonymous = True" in out
    assert "<<main>>" in out


def test_label():
    out = weave(md_in, "label")
    assert out.count('<div class="entangled-code-block" markdown="1">') == 2
    assert '<code>file: hello.py</code>' in out
    assert '<code>#main</code>' in out
    assert "\n\n``` {.python file=hello.py}\n<<main>>\n```\n\n</div>\n\n" in out
    assert "\n\n``` {.python}\nanonymous = True\n```\n" in out


def test_label_indented_without_trailing_newline():
    text = "- item\n\n    ``` {.python #a}\n    x = 1\n    ```"
    out = weave(text, "label")
    assert out.endswith("    ```\n\n    </div>\n\n")
    assert "    <div class=\"entangled-code-block\" markdown=\"1\">\n" in out


def test_label_and_title_compose():
    out = weave(md_in, "label", "title")
    assert '<code>#main</code></div>\n\n```python {#main .extra title="#main"}\n' in out


def test_weave_command(tmp_path: Path, capsys: pytest.CaptureFixture[str]):
    with chdir(tmp_path):
        Path("input.md").write_text(md_in)
        main(args=["weave", "-f", "title", "-o", "output.md", "input.md"], standalone_mode=False)
        assert '```python {title="file: hello.py"}' in Path("output.md").read_text()

        main(args=["weave", "input.md"], standalone_mode=False)
        assert '<code>#main</code>' in capsys.readouterr().out

        main(args=["weave", "--list-filters"], standalone_mode=False)
        out = capsys.readouterr().out
        assert all(name in out for name in filters)
