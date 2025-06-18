from typing import List
import requests
from trafilatura import extract as trafilatura_extract
from extractors.base import ContentExtractor, ContentItem
from utils.markdown import html_to_markdown

class SubstackExtractor(ContentExtractor):
    def can_handle(self, source: str) -> bool:
        return 'substack.com' in source

    def extract(self, source: str) -> List[ContentItem]:
        resp = requests.get(source, timeout=10)
        resp.raise_for_status()
        html = resp.text
        main_content = trafilatura_extract(html, include_comments=False, include_tables=True)
        if not main_content:
            return []
        markdown = html_to_markdown(main_content)
        # Try to extract title
        from bs4 import BeautifulSoup
        soup = BeautifulSoup(html, 'html.parser')
        title = soup.title.string.strip() if soup.title else source
        return [ContentItem(
            title=title,
            content=markdown,
            content_type='blog',
            source_url=source,
            author='',
            user_id=''
        )] 