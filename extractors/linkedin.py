from typing import List
import requests
from bs4 import BeautifulSoup
from extractors.base import ContentExtractor, ContentItem
from utils.markdown import html_to_markdown

class LinkedInExtractor(ContentExtractor):
    def can_handle(self, source: str) -> bool:
        return 'linkedin.com' in source

    def extract(self, source: str) -> List[ContentItem]:
        resp = requests.get(source, timeout=10)
        resp.raise_for_status()
        html = resp.text
        soup = BeautifulSoup(html, 'html.parser')
        # Heuristic: find main post content
        post_div = soup.find('div', {'class': 'break-words'})
        if not post_div:
            return []
        markdown = html_to_markdown(str(post_div))
        title = soup.title.string.strip() if soup.title else source
        return [ContentItem(
            title=title,
            content=markdown,
            content_type='linkedin_post',
            source_url=source,
            author='',
            user_id=''
        )] 