from typing import List
import os
from extractors.base import ContentExtractor, ContentItem
from utils.markdown import text_to_markdown

class GenericExtractor(ContentExtractor):
    def can_handle(self, source: str) -> bool:
        return True  # Fallback

    def extract(self, source: str) -> List[ContentItem]:
        # Try to read as text
        if os.path.isfile(source):
            with open(source, 'r', encoding='utf-8') as f:
                text = f.read()
            markdown = text_to_markdown(text)
            return [ContentItem(
                title=os.path.basename(source),
                content=markdown,
                content_type='other',
                source_url=None,
                author='',
                user_id=''
            )]
        return [] 