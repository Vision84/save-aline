#!/usr/bin/env python3
import click
import json
from pathlib import Path
from typing import Optional
from rich.console import Console
from rich.logging import RichHandler
import logging

from utils.router import ContentRouter
from extractors.base import ContentItem

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format="%(message)s",
    datefmt="[%X]",
    handlers=[RichHandler(rich_tracebacks=True)]
)
logger = logging.getLogger("scraper")
console = Console()

@click.command()
@click.option('--source', required=True, help='URL or file path to extract content from')
@click.option('--team-id', required=True, help='Team identifier for the output')
@click.option('--output', default='output.json', help='Output file path')
@click.option('--force-content-type', help='Override content type detection')
@click.option('--max-items', type=int, help='Maximum number of items to extract')
def main(source: str, team_id: str, output: str, force_content_type: Optional[str], max_items: Optional[int]):
    """Extract content from various sources and output in a standardized format."""
    try:
        router = ContentRouter()
        extractor = router.get_extractor(source)
        if not extractor:
            logger.error(f"No suitable extractor found for source: {source}")
            return
        
        logger.info(f"Starting extraction from: {source}")
        items = extractor.extract(source)
        
        # Apply max_items limit if specified
        if max_items and len(items) > max_items:
            logger.info(f"Limiting output to {max_items} items (found {len(items)})")
            items = items[:max_items]
        
        skipped = 0
        processed_items = []
        
        for item in items:
            if force_content_type:
                item.content_type = force_content_type
            elif not item.content_type:
                item.content_type = router.infer_content_type(source, item.content)
            
            if not item.content:
                skipped += 1
                continue
                
            # Use model_dump() instead of dict() for Pydantic v2 compatibility
            try:
                processed_items.append(item.model_dump())
            except AttributeError:
                # Fallback for older Pydantic versions
                processed_items.append(item.dict())
        
        output_data = {
            "team_id": team_id,
            "items": processed_items
        }
        
        # Ensure output directory exists
        output_path = Path(output)
        output_path.parent.mkdir(parents=True, exist_ok=True)
        
        with open(output, 'w', encoding='utf-8') as f:
            json.dump(output_data, f, indent=2, ensure_ascii=False)
        
        logger.info(f"Successfully extracted {len(processed_items)} items to {output}")
        if processed_items:
            content_type = force_content_type or processed_items[0].get('content_type', 'unknown')
            logger.info(f"Content type: {content_type}")
        if skipped:
            logger.warning(f"Skipped {skipped} items due to empty content.")
            
    except Exception as e:
        logger.error(f"Error processing source: {str(e)}")
        raise click.Abort()

if __name__ == '__main__':
    main() 