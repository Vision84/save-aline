# Save-Aline Web Scraper

A robust, extensible web scraper for extracting blog posts, guides, and articles from a variety of sources (websites, PDFs, Reddit, Substack, LinkedIn, Google Drive, and more). Outputs standardized JSON for downstream use.

## Requirements
- Python 3.8+
- Google Chrome (for Selenium fallback)
- ChromeDriver (automatically managed by `webdriver_manager`)

## Installation
1. Clone the repository:
   ```bash
   git clone <repo-url>
   cd save-aline
   ```
2. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

## Usage
Run the scraper from the command line:

```bash
python scrape.py --source <URL-or-file> --team-id <team-name> [--output <output.json>] [--max-items N] [--force-content-type <type>]
```

### Options
- `--source` (required): URL or file path to extract content from (e.g., a blog, PDF, or article page)
- `--team-id` (required): Team identifier for the output JSON
- `--output`: Output file path (default: `output.json`)
- `--max-items`: Maximum number of items to extract (optional)
- `--force-content-type`: Override automatic content type detection (optional)

### Example
```bash
python scrape.py --source "https://interviewing.io/blog" --team-id "test-team" --output "output.json" --max-items 5
```

## Output
The output is a JSON file with the following structure:
```json
{
  "team_id": "test-team",
  "items": [
    {
      "title": "Blog Post Title",
      "content": "...markdown content...",
      "content_type": "blog",
      "source_url": "https://...",
      "author": "",
      "user_id": ""
    },
    ...
  ]
}
```

## Adding New Extractors
- To support new content types, add a new extractor class in the `extractors/` directory and register it in `utils/router.py`.
- See existing extractors (e.g., `WebsiteExtractor`, `PDFExtractor`) for examples.

## Configuration
- Centralized config is in `config.py` (headers, Selenium options, URL patterns, etc.).
- Adjust as needed for custom deployments or new sites.

## Selenium/ChromeDriver Notes
- For dynamic sites, Selenium is used as a fallback. Requires Google Chrome and ChromeDriver (auto-managed).
- If you encounter ChromeDriver errors, ensure Chrome is installed and up to date.

## Troubleshooting
- **ChromeDriver errors**: Make sure Chrome is installed and matches the ChromeDriver version. Try updating both.
- **Missing dependencies**: Run `pip install -r requirements.txt`.
- **Permission errors**: Try running with elevated permissions or check file paths.
- **No content extracted**: Check the URL, or try running with `--max-items 1` to debug.

## Contributing
Pull requests and issues are welcome! Please open an issue to discuss major changes.

## License
MIT License

## Author
Arnav Bonigala