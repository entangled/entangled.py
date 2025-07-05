from entangled.markdown_reader import read_markdown_string
from entangled.hooks.spdx_license import Hook as SPDXLicense
from entangled.tangle import tangle_ref, AnnotationMethod
from entangled.code_reader import CodeReader
from entangled.commands.stitch import stitch_markdown

input_md = """
A C file with a license!

``` {.c file=test.c}
// SPDX-License-Identifier: MIT
#include <stdio.h>

int main() {
    printf("Hello, World!\n");
    return 0;
}
```
"""

output_test_c = """// SPDX-License-Identifier: MIT
/* ~/~ begin <<-#test.c>>[init] */
#include <stdio.h>

int main() {
    printf("Hello, World!\n");
    return 0;
}
/* ~/~ end */
"""

output_test_c_modified = """// SPDX-License-Identifier: MIT
# ~/~ begin <<-#test.c>>[init]

int main() {
    printf("Hello, World!\n");
    return 0;
}
# ~/~ end
"""

input_md_modified = """
A C file with a license!

``` {.c file=test.c}
// SPDX-License-Identifier: MIT

int main() {
    printf("Hello, World!\n");
    return 0;
}
```
"""


def test_spdx_license():
    hooks = [SPDXLicense(SPDXLicense.Config())]
    refs, content = read_markdown_string(input_md, hooks=hooks)
    assert "test.c" in refs
    print(next(refs["test.c"]))
    assert next(refs["test.c"]).header == "// SPDX-License-Identifier: MIT"
    code_content, _ = tangle_ref(refs, "test.c", AnnotationMethod.STANDARD)
    print(code_content.strip())
    print(output_test_c.strip())
    assert code_content.strip() == output_test_c.strip()

    cr = CodeReader("test.c", refs)
    cr.run(output_test_c_modified)
    md_content = stitch_markdown(refs, content)
    assert md_content.strip() == input_md_modified.strip()
