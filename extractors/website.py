from typing import List
import requests
from bs4 import BeautifulSoup
from trafilatura import extract as trafilatura_extract
from extractors.base import ContentExtractor, ContentItem
from utils.markdown import html_to_markdown
import re
from urllib.parse import urljoin, urlparse
import os
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.common.action_chains import ActionChains
from webdriver_manager.chrome import ChromeDriverManager
import logging
import time
from selenium.webdriver.chrome.service import Service

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class WebsiteExtractor(ContentExtractor):
    def can_handle(self, source: str) -> bool:
        return source.startswith('http')

    def extract(self, source: str) -> List[ContentItem]:
        logger.info(f"Starting extraction for source: {source}")
        
        # Crawl index if needed
        urls = self._discover_urls(source)
        logger.info(f"Discovered {len(urls)} URLs to process")
        
        items = []
        for url in urls:
            try:
                logger.info(f"Processing URL: {url}")
                resp = requests.get(url, timeout=15, headers={
                    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
                })
                resp.raise_for_status()
                html = resp.text
                soup = BeautifulSoup(html, 'html.parser')

                # Try to find blog post containers by common blog-like classes
                post_divs = soup.find_all(
                    lambda tag: tag.name == 'div' and (
                        ('bg-white' in tag.get('class', []) and 'p-[30px]' in tag.get('class', []))
                        or 'blog-post' in tag.get('class', [])
                        or 'post' in tag.get('class', [])
                        or 'article' in tag.get('class', [])
                    )
                )
                logger.info(f"Found {len(post_divs)} post divs")
                
                article_links = []
                for div in post_divs:
                    # Try to find a link or button to the full article
                    link = None
                    a_tag = div.find('a', href=True)
                    if a_tag:
                        link = a_tag['href']
                        logger.info(f"Found link in a tag: {link}")
                    else:
                        button = div.find('button')
                        if button and button.parent.name == 'a' and button.parent.has_attr('href'):
                            link = button.parent['href']
                            logger.info(f"Found link in button parent: {link}")
                    if link:
                        full_url = urljoin(url, link)
                        article_links.append(full_url)

                logger.info(f"Found {len(article_links)} article links")

                # If we found article links, visit each and extract full content
                if article_links:
                    for article_url in article_links:
                        try:
                            logger.info(f"Extracting from article URL: {article_url}")
                            article_resp = requests.get(article_url, timeout=15, headers={
                                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
                            })
                            article_resp.raise_for_status()
                            article_html = article_resp.text
                            article_soup = BeautifulSoup(article_html, 'html.parser')
                            
                            # Extract title
                            title_elem = article_soup.find(['h1', 'h2'])
                            title = title_elem.get_text(strip=True) if title_elem else article_url
                            
                            # Extract date
                            date_elem = article_soup.find('time') or article_soup.find(['h4', 'span'], class_=lambda c: c and 'text-slate-500' in c and 'text-sm' in c)
                            date = date_elem.get_text(strip=True) if date_elem else ''
                            
                            # Extract main content
                            main_content_elem = article_soup.find('main') or article_soup.find('article')
                            if not main_content_elem:
                                # Try to find the largest content div
                                content_divs = article_soup.find_all('div')
                                if content_divs:
                                    main_content_elem = max(content_divs, key=lambda d: len(d.get_text()))
                            
                            content_html = str(main_content_elem) if main_content_elem else article_html
                            markdown = html_to_markdown(content_html)
                            
                            if date:
                                markdown = f"Date: {date}\n\n{markdown}"
                            
                            items.append(ContentItem(
                                title=title,
                                content=markdown,
                                content_type='blog',
                                source_url=article_url,
                                author='',
                                user_id=''
                            ))
                            logger.info(f"Successfully extracted article: {title}")
                        except Exception as e:
                            logger.error(f"Error extracting from {article_url}: {e}")
                            continue
                    continue

                # If no article links found, try Selenium as a fallback
                if not article_links and post_divs:
                    logger.info("No article links found, trying Selenium fallback")
                    items.extend(self._extract_with_selenium(url))
                    continue

                # Fallback: Use trafilatura for main content extraction
                logger.info("Using trafilatura fallback")
                main_content = trafilatura_extract(html, include_comments=False, include_tables=True)
                if not main_content:
                    logger.warning("No main content found with trafilatura")
                    continue
                markdown = html_to_markdown(main_content)
                title = self._extract_title(html)
                items.append(ContentItem(
                    title=title or url,
                    content=markdown,
                    content_type='blog',
                    source_url=url,
                    author='',
                    user_id=''
                ))
                logger.info(f"Successfully extracted with trafilatura: {title}")
            except Exception as e:
                logger.error(f"Error processing {url}: {e}")
                continue
        
        logger.info(f"Total items extracted: {len(items)}")
        return items

    def _extract_with_selenium(self, url: str) -> List[ContentItem]:
        """Selenium fallback for extracting content when no direct links are found"""
        logger.info(f"Starting Selenium fallback extraction for: {url}")
        
        options = Options()
        options.add_argument('--headless')  # Run headless for production
        options.add_argument('--no-sandbox')
        options.add_argument('--disable-dev-shm-usage')
        options.add_argument('--disable-gpu')
        options.add_argument('--window-size=1920,1080')
        options.add_argument('--user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36')
        
        driver = None
        items = []
        try:
            # Use the modern Selenium approach without executable_path
            service = Service(ChromeDriverManager().install())
            driver = webdriver.Chrome(service=service, options=options)
            logger.info("Chrome driver initialized")
            
            driver.get(url)
            logger.info(f"Loaded page: {driver.current_url}")
            driver.implicitly_wait(5)

            # Wait for page to load completely
            time.sleep(3)
            
            # First pass: collect all URLs we can find
            article_urls = set()
            
            # Look for "Read more" buttons and get their URLs
            read_more_buttons = driver.find_elements(By.XPATH, "//*[contains(text(), 'Read more') or contains(text(), 'Read More') or contains(text(), 'Continue reading') or contains(text(), 'Read article') or contains(text(), 'View post')]")
            logger.info(f"Found {len(read_more_buttons)} 'Read more' buttons")
            
            for i, btn in enumerate(read_more_buttons):
                try:
                    # Try to get the URL from the button's parent link or data attributes
                    parent_link = None
                    try:
                        parent_link = btn.find_element(By.XPATH, "./ancestor::a[contains(@href, '/blog/') or contains(@href, '/post/') or contains(@href, '/article/') or contains(@href, '/news/')]")
                    except Exception:
                        pass
                    
                    if parent_link:
                        href = parent_link.get_attribute('href')
                        if href:
                            article_urls.add(href)
                            logger.info(f"Found article URL from button {i}: {href}")
                    else:
                        # Try to click the button and see if it navigates
                        try:
                            btn.click()
                            time.sleep(2)
                            current_url = driver.current_url
                            if current_url != url and self._is_article_url(current_url):
                                article_urls.add(current_url)
                                logger.info(f"Found article URL from button click {i}: {current_url}")
                            driver.back()
                            time.sleep(1)
                        except Exception as e:
                            logger.warning(f"Could not click button {i}: {e}")
                            continue
                except Exception as e:
                    logger.warning(f"Error processing button {i}: {e}")
                    continue
            
            # Also look for any links that might be article links
            all_links = driver.find_elements(By.TAG_NAME, "a")
            for link in all_links:
                try:
                    href = link.get_attribute('href')
                    if href and self._is_article_url(href):
                        article_urls.add(href)
                except Exception:
                    continue
            
            logger.info(f"Total article URLs found: {len(article_urls)}")
            
            # Now extract content from each article URL
            for article_url in article_urls:
                try:
                    logger.info(f"Extracting content from: {article_url}")
                    driver.get(article_url)
                    time.sleep(2)
                    
                    # Extract title
                    title_elem = driver.find_element(By.TAG_NAME, "h1")
                    title = title_elem.text if title_elem else article_url
                    
                    # Extract content
                    content_elem = driver.find_element(By.TAG_NAME, "body")
                    content_html = content_elem.get_attribute('innerHTML')
                    
                    # Use trafilatura to clean the content
                    main_content = trafilatura_extract(content_html, include_comments=False, include_tables=True)
                    if not main_content:
                        logger.warning(f"No main content found for {article_url}")
                        continue
                    
                    markdown = html_to_markdown(main_content)
                    
                    items.append(ContentItem(
                        title=title,
                        content=markdown,
                        content_type='blog',
                        source_url=article_url,
                        author='',
                        user_id=''
                    ))
                    logger.info(f"Successfully extracted: {title}")
                except Exception as e:
                    logger.error(f"Error extracting from {article_url}: {e}")
                    continue
                    
        except Exception as e:
            logger.error(f"Error in Selenium extraction: {e}")
        finally:
            if driver:
                driver.quit()
                logger.info("Chrome driver closed")
        
        return items

    def _extract_quill_posts(self, html: str, base_url: str) -> List[ContentItem]:
        """Extract posts from Quill-based websites (like interviewing.io)"""
        soup = BeautifulSoup(html, 'html.parser')
        items = []
        
        # Look for Quill post containers
        post_containers = soup.find_all('div', class_=lambda c: c and 'quill' in c.lower())
        
        for container in post_containers:
            try:
                # Extract title
                title_elem = container.find(['h1', 'h2', 'h3'])
                title = title_elem.get_text(strip=True) if title_elem else "Untitled"
                
                # Extract content
                content_elem = container.find('div', class_=lambda c: c and 'content' in c.lower())
                if not content_elem:
                    content_elem = container
                
                content_html = str(content_elem)
                markdown = html_to_markdown(content_html)
                
                items.append(ContentItem(
                    title=title,
                    content=markdown,
                    content_type='blog',
                    source_url=base_url,
                    author='',
                    user_id=''
                ))
            except Exception as e:
                logger.error(f"Error extracting Quill post: {e}")
                continue
        
        return items

    def _discover_urls(self, source: str) -> List[str]:
        """Discover URLs to extract content from."""
        try:
            # If it's already an article URL, return it directly
            if self._is_article_url(source):
                return [source]
            
            # Try to crawl the page to find article links
            resp = requests.get(source, timeout=15, headers={
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
            })
            resp.raise_for_status()
            soup = BeautifulSoup(resp.text, 'html.parser')
            
            # Find all links on the page
            links = set()
            for a in soup.find_all('a', href=True):
                href = a['href']
                full_url = urljoin(source, href)
                
                # Only include article URLs
                if self._is_article_url(full_url):
                    links.add(full_url)
            
            # If we found article links, return them
            if links:
                logger.info(f"Found {len(links)} article URLs to process")
                return list(links)
            
            # If no article links found, treat the source as a single article
            logger.info("No article links found, treating source as single article")
            return [source]
            
        except Exception as e:
            logger.error(f"Error discovering URLs from {source}: {e}")
            return [source]

    def _is_article_url(self, url: str) -> bool:
        """Check if a URL is likely to be an article."""
        if not url:
            return False
        
        # Skip common non-article patterns
        skip_patterns = [
            '/category/', '/tag/', '/author/', '/page/', '/search',
            '/about', '/contact', '/privacy', '/terms', '/login',
            '/register', '/subscribe', '/newsletter', '/feed',
            '/sitemap', '/robots.txt', '/favicon', '/ads',
            'javascript:', 'mailto:', 'tel:', '#'
        ]
        
        url_lower = url.lower()
        for pattern in skip_patterns:
            if pattern in url_lower:
                return False
        
        # Look for article-like patterns
        article_patterns = [
            '/blog/', '/post/', '/article/', '/news/', '/story/',
            '/202', '/2023/', '/2024/', '/2025/',
            '.html', '.php', '.asp'
        ]
        
        for pattern in article_patterns:
            if pattern in url_lower:
                return True
        
        # If it's a direct URL with a slug-like structure, it might be an article
        parsed = urlparse(url)
        path_parts = parsed.path.strip('/').split('/')
        
        # If the path has 2+ parts and looks like a slug, it's probably an article
        if len(path_parts) >= 2 and all(len(part) > 3 for part in path_parts[-2:]):
            return True
        
        return False

    def _extract_title(self, html: str) -> str:
        """Extract title from HTML."""
        soup = BeautifulSoup(html, 'html.parser')
        
        # Try different title selectors
        title_selectors = [
            'h1',
            'title',
            '[class*="title"]',
            '[class*="heading"]',
            'h2',
            'h3'
        ]
        
        for selector in title_selectors:
            title_elem = soup.select_one(selector)
            if title_elem:
                title = title_elem.get_text(strip=True)
                if title and len(title) > 5:
                    return title
        
        return "Untitled" 