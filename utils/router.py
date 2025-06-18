from typing import List, Optional
from pathlib import Path
import mimetypes
from urllib.parse import urlparse

from extractors.base import ContentExtractor, ContentItem
from extractors.website import WebsiteExtractor
from extractors.pdf import PDFExtractor
from extractors.reddit import RedditExtractor
from extractors.substack import SubstackExtractor
from extractors.linkedin import LinkedInExtractor
from extractors.transcript import TranscriptExtractor
from extractors.generic import GenericExtractor
from extractors.gdrive import GoogleDriveExtractor

class ContentRouter:
    """Routes content extraction to the appropriate extractor."""
    
    def __init__(self):
        self.extractors: List[ContentExtractor] = [
            GoogleDriveExtractor(),  # Put Google Drive first to catch drive.google.com URLs
            WebsiteExtractor(),
            PDFExtractor(),
            RedditExtractor(),
            SubstackExtractor(),
            LinkedInExtractor(),
            TranscriptExtractor(),
            GenericExtractor(),
        ]
    
    def get_extractor(self, source: str) -> Optional[ContentExtractor]:
        """Find the appropriate extractor for the given source."""
        for extractor in self.extractors:
            if extractor.can_handle(source):
                return extractor
        return GenericExtractor()
    
    def infer_content_type(self, source: str, content: str) -> str:
        """Infer the content type based on source and content."""
        # Check if it's a file
        if Path(source).exists():
            mime_type, _ = mimetypes.guess_type(source)
            if mime_type == 'application/pdf':
                return 'book'
            if mime_type == 'text/plain':
                return 'call_transcript'
        
        # Check URL patterns
        parsed_url = urlparse(source)
        domain = parsed_url.netloc.lower()
        
        if 'reddit.com' in domain:
            return 'reddit_comment'
        if 'linkedin.com' in domain:
            return 'linkedin_post'
        if 'substack.com' in domain:
            return 'blog'
        
        # Default to blog for web content
        return 'blog' 