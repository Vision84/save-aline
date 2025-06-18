from typing import List
import os
from extractors.base import ContentExtractor, ContentItem
from utils.markdown import text_to_markdown

class TranscriptExtractor(ContentExtractor):
    def can_handle(self, source: str) -> bool:
        return os.path.isfile(source) and source.lower().endswith('.txt')

    def extract(self, source: str) -> List[ContentItem]:
        with open(source, 'r', encoding='utf-8') as f:
            text = f.read()
        markdown = text_to_markdown(text)
        return [ContentItem(
            title=os.path.basename(source),
            content=markdown,
            content_type='call_transcript',
            source_url=None,
            author='',
            user_id=''
        )] 