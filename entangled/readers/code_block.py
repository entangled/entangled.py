from ..document import CodeBlock, Content
from ..config import Config
from .types import InputStream, Reader, MarkdownStream
from .delimiters import delimited_token_getter


def code_block(config: Config) -> Reader[Content, None, CodeBlock | None]:
    get_raw_token = delimited_token_getter(config.markers.open, config.markers.close)

    def code_block_reader(input: InputStream) -> MarkdownStream[CodeBlock | None]:
        block = get_raw_token(input)
        if block is None:
            return None

    return code_block_reader
