from markdownify import markdownify as md
import re

def html_to_markdown(html: str) -> str:
    return md(html, heading_style="ATX")
 
def text_to_markdown(text: str) -> str:
    """Convert plain text to well-formatted markdown"""
    if not text:
        return ""
    
    # Clean up the text
    text = text.strip()
    
    # Split into lines and process
    lines = text.split('\n')
    markdown_lines = []
    
    for i, line in enumerate(lines):
        line = line.strip()
        if not line:
            continue
            
        # Detect and format headings
        if re.match(r'^CHAPTER\s+\d+', line, re.IGNORECASE):
            # Convert "CHAPTER 1" to "# Chapter 1"
            chapter_match = re.match(r'^CHAPTER\s+(\d+)(.*)', line, re.IGNORECASE)
            if chapter_match:
                chapter_num = chapter_match.group(1)
                chapter_title = chapter_match.group(2).strip()
                if chapter_title:
                    markdown_lines.append(f"# Chapter {chapter_num}: {chapter_title}")
                else:
                    markdown_lines.append(f"# Chapter {chapter_num}")
            else:
                markdown_lines.append(f"# {line}")
        elif re.match(r'^\d+\.\s+', line):
            # Numbered lists
            markdown_lines.append(line)
        elif re.match(r'^[A-Z][A-Z\s]+$', line) and len(line) > 3:
            # All caps lines that might be headings
            markdown_lines.append(f"## {line.title()}")
        elif line.endswith(':') and len(line) < 100:
            # Lines ending with colon might be section headers
            markdown_lines.append(f"### {line}")
        else:
            # Regular paragraph text
            markdown_lines.append(line)
    
    # Join lines with proper spacing
    result = '\n\n'.join(markdown_lines)
    
    # Clean up excessive whitespace
    result = re.sub(r'\n{3,}', '\n\n', result)
    
    return result 