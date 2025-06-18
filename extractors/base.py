from abc import ABC, abstractmethod
from typing import List, Dict, Optional
from pydantic import BaseModel

class ContentItem(BaseModel):
    title: str
    content: str
    content_type: str
    source_url: Optional[str] = None
    author: Optional[str] = None
    user_id: Optional[str] = None

class ContentExtractor(ABC):
    """Base class for all content extractors."""
    
    @abstractmethod
    def extract(self, source: str) -> List[ContentItem]:
        """
        Extract content from the given source.
        
        Args:
            source: URL or file path to extract content from
            
        Returns:
            List of ContentItem objects containing the extracted content
        """
        pass
    
    @abstractmethod
    def can_handle(self, source: str) -> bool:
        """
        Determine if this extractor can handle the given source.
        
        Args:
            source: URL or file path to check
            
        Returns:
            True if this extractor can handle the source, False otherwise
        """
        pass 