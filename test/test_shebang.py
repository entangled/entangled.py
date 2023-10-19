from entangled.markdown_reader import MarkdownReader
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
    md = MarkdownReader("-")
    md.run(input_md)
    assert "test.sh" in md.reference_map
    assert next(md.reference_map["test.sh"]).header == "#!/bin/bash"
    content, _ = tangle_ref(md.reference_map, "test.sh", AnnotationMethod.STANDARD)
    assert content.strip() == output_test_sh.strip()

    cr = CodeReader("test.sh", md.reference_map)
    cr.run(output_test_sh_modified)
    md_content = stitch_markdown(md.reference_map, md.content)
    assert md_content.strip() == input_md_modified.strip()
