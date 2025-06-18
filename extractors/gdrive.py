from typing import List
import os
import re
import requests
import logging
from bs4 import BeautifulSoup
from extractors.base import ContentExtractor, ContentItem
from extractors.pdf import PDFExtractor

# Set up logging
logger = logging.getLogger(__name__)

class GoogleDriveExtractor(ContentExtractor):
    def can_handle(self, source: str) -> bool:
        return 'drive.google.com/drive/folders/' in source

    def extract(self, source: str) -> List[ContentItem]:
        logger.info(f"Starting Google Drive extraction for: {source}")
        # Scrape the folder page for PDF links
        resp = requests.get(source, timeout=15)
        resp.raise_for_status()
        html_content = resp.text
        logger.info(f"Retrieved HTML content, length: {len(html_content)}")
        
        soup = BeautifulSoup(html_content, 'html.parser')
        pdf_links = self._find_pdf_links(soup)
        logger.info(f"Found {len(pdf_links)} PDF links")
        
        # Deduplicate by URL to avoid processing the same PDF multiple times
        unique_pdf_links = []
        seen_urls = set()
        for pdf_url, pdf_name in pdf_links:
            if pdf_url not in seen_urls:
                unique_pdf_links.append((pdf_url, pdf_name))
                seen_urls.add(pdf_url)
        
        logger.info(f"After deduplication: {len(unique_pdf_links)} unique PDF links")
        
        items = []
        for pdf_url, pdf_name in unique_pdf_links:
            try:
                logger.info(f"Processing PDF: {pdf_name} from {pdf_url}")
                local_path = self._download_pdf(pdf_url, pdf_name)
                pdf_items = PDFExtractor().extract(local_path)
                for item in pdf_items:
                    item.source_url = pdf_url
                items.extend(pdf_items)
                os.remove(local_path)
                logger.info(f"Successfully processed PDF: {pdf_name}")
            except Exception as e:
                logger.error(f"Error processing PDF {pdf_name}: {e}")
                continue
        logger.info(f"Google Drive extraction completed. Total items: {len(items)}")
        return items

    def _find_pdf_links(self, soup):
        # Google Drive folder page: look for JavaScript data structures containing file info
        links = []
        logger.info("Searching for PDF links in Google Drive folder...")
        
        # Look for JavaScript data structures that contain file information
        script_tags = soup.find_all('script')
        for script in script_tags:
            if script.string:
                script_content = script.string
                # Look for file data patterns in the JavaScript
                if 'application/pdf' in script_content:
                    logger.info("Found PDF data in JavaScript")
                    # Extract file IDs and names from the JavaScript data
                    import re
                    
                    # Pattern to match file data: file ID, name, and type
                    # This matches the pattern we saw in the HTML
                    file_pattern = r'"([A-Za-z0-9_-]{25,})"\s*,\s*\[[^\]]+\]\s*,\s*"([^"]+\.pdf)"\s*,\s*"application/pdf"'
                    matches = re.findall(file_pattern, script_content)
                    
                    for file_id, file_name in matches:
                        # Validate file ID format (Google Drive IDs are typically 25+ characters)
                        if len(file_id) >= 25 and file_id.isalnum() or '-' in file_id or '_' in file_id:
                            # Convert to direct download link
                            direct_url = f'https://drive.google.com/uc?export=download&id={file_id}'
                            links.append((direct_url, file_name))
                            logger.info(f"Found PDF link: {file_name} -> {direct_url}")
        
        # Fallback: also look for hrefs to /file/d/ID/view?usp=drive_link (original method)
        for a in soup.find_all('a', href=True):
            href = a['href']
            logger.debug(f"Found link: {a.text.strip()} -> {href}")
            if re.search(r'/file/d/.+/view', href) and ('.pdf' in a.text.lower() or '.pdf' in href.lower()):
                # Try to get the file name from the link text or href
                name = a.text.strip() or href.split('/')[-2] + '.pdf'
                # Convert to direct download link
                file_id = re.search(r'/file/d/([^/]+)', href)
                if file_id:
                    file_id = file_id.group(1)
                    direct_url = f'https://drive.google.com/uc?export=download&id={file_id}'
                    links.append((direct_url, name))
                    logger.info(f"Found PDF link from HTML: {name} -> {direct_url}")
        
        logger.info(f"Total PDF links found: {len(links)}")
        return links

    def _download_pdf(self, url, name):
        resp = requests.get(url, timeout=30)
        resp.raise_for_status()
        local_path = f'_gdrive_{name.replace(" ", "_")}'
        with open(local_path, 'wb') as f:
            f.write(resp.content)
        return local_path 