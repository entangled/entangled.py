from entangled.tangle import MarkdownReader
from entangled.document import retrieve_markdown


def test_retrieve_same_content(markdown):
    md = MarkdownReader("test")
    md.run(markdown)
    # print(retrieve_markdown(md.reference_map, md.content))
    assert retrieve_markdown(md.reference_map, md.content) == markdown
