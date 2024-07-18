from entangled.markdown_reader import read_markdown_string
from entangled.hooks.shebang import Hook as Shebang
from entangled.tangle import tangle_ref, AnnotationMethod
from entangled.code_reader import CodeReader
from entangled.commands.stitch import stitch_markdown

input_md = """
A script with a she-bang!

``` {.bash file=test.sh}
#!/bin/bash

echo "Hello, World!"
```
"""

output_test_sh = """#!/bin/bash
# ~/~ begin <<-#test.sh>>[init]

echo "Hello, World!"
# ~/~ end
"""

output_test_sh_modified = """#!/bin/bash
# ~/~ begin <<-#test.sh>>[init]

echo "Hello, Universe!"
# ~/~ end
"""

input_md_modified = """
A script with a she-bang!

``` {.bash file=test.sh}
#!/bin/bash

echo "Hello, Universe!"
```
"""


def test_shebang():
    hooks = [Shebang(Shebang.Config())]
    refs, content = read_markdown_string(input_md, hooks=hooks)
    assert "test.sh" in refs
    assert next(refs["test.sh"]).header == "#!/bin/bash"
    code_content, _ = tangle_ref(refs, "test.sh", AnnotationMethod.STANDARD)
    assert code_content.strip() == output_test_sh.strip()

    cr = CodeReader("test.sh", refs)
    cr.run(output_test_sh_modified)
    md_content = stitch_markdown(refs, content)
    assert md_content.strip() == input_md_modified.strip()
