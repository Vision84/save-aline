from typing import List
import requests
from extractors.base import ContentExtractor, ContentItem
from utils.markdown import html_to_markdown
import re

class RedditExtractor(ContentExtractor):
    def can_handle(self, source: str) -> bool:
        return 'reddit.com' in source

    def extract(self, source: str) -> List[ContentItem]:
        # Try to get comment via Reddit JSON API
        api_url = self._to_json_url(source)
        try:
            resp = requests.get(api_url, headers={'User-agent': 'Mozilla/5.0'})
            resp.raise_for_status()
            data = resp.json()
            comment = self._extract_comment(data)
            if comment:
                markdown = html_to_markdown(comment['body_html'])
                return [ContentItem(
                    title=f"Reddit comment by {comment.get('author', '')}",
                    content=markdown,
                    content_type='reddit_comment',
                    source_url=source,
                    author=comment.get('author', ''),
                    user_id=comment.get('author_fullname', '')
                )]
        except Exception:
            pass
        # Fallback: scrape HTML
        return []

    def _to_json_url(self, url: str) -> str:
        if not url.endswith('.json'):
            if url.endswith('/'): url = url[:-1]
            url += '.json'
        return url

    def _extract_comment(self, data) -> dict:
        # Reddit JSON structure: [post, [comments]]
        try:
            comments = data[1]['data']['children']
            if comments:
                return comments[0]['data']
        except Exception:
            return None
        return None 