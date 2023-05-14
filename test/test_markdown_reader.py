from entangled.markdown_reader import MarkdownReader
from entangled.document import retrieve_markdown


def test_retrieve_same_content(data):
    file = data / "hello-world" / "hello-world.md"
    with open(file, "r") as f:
        md = MarkdownReader(str(file))
        markdown = f.read()
        md.run(markdown)
        assert retrieve_markdown(md.reference_map, md.content) == markdown
