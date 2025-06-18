from typing import List
from PyPDF2 import PdfReader
from extractors.base import ContentExtractor, ContentItem
from utils.markdown import text_to_markdown
import os

class PDFExtractor(ContentExtractor):
    def can_handle(self, source: str) -> bool:
        return os.path.isfile(source) and source.lower().endswith('.pdf')

    def extract(self, source: str) -> List[ContentItem]:
        reader = PdfReader(source)
        items = []
        text = ''
        for page in reader.pages:
            text += page.extract_text() or ''
        
        # For now, treat the entire PDF as one item to avoid fragmentation
        # You can uncomment the chapter extraction if you want more granular items
        markdown = text_to_markdown(text)
        items.append(ContentItem(
            title=os.path.basename(source).replace('.pdf', ''),
            content=markdown,
            content_type='book',
            source_url=None,
            author='',
            user_id=''
        ))
        
        return items

    def _extract_chapters(self, text: str) -> List[tuple]:
        """Extract chapters with their actual titles"""
        import re
        
        # Find all chapter matches with their content
        chapter_pattern = r'(chapter\s+\d+[^\n]*)\n(.*?)(?=chapter\s+\d+|\Z)'
        matches = re.findall(chapter_pattern, text, re.DOTALL | re.IGNORECASE)
        
        chapters = []
        for match in matches:
            chapter_title = match[0].strip()
            chapter_content = match[1].strip()
            if chapter_content:  # Only add if there's actual content
                chapters.append((chapter_title, chapter_content))
        
        # If no chapters found, treat the whole text as one item
        if not chapters:
            chapters = [("Document", text.strip())]
            
        return chapters 