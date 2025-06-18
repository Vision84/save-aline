import os
import json
import pytest
import subprocess
from pathlib import Path

PROJECT_ROOT = Path(__file__).parent.parent.resolve()
PYTHON_BIN = PROJECT_ROOT / "venv/bin/python"
SCRAPE_SCRIPT = PROJECT_ROOT / "scrape.py"

def run_cli(source, team_id="aline123", output="test_output.json", force_content_type=None):
    cmd = [str(PYTHON_BIN), str(SCRAPE_SCRIPT), "--source", source, "--team-id", team_id, "--output", output]
    if force_content_type:
        cmd += ["--force-content-type", force_content_type]
    result = subprocess.run(cmd, capture_output=True, text=True)
    return result

def validate_output(output_path, expect_items=True):
    assert os.path.exists(output_path)
    with open(output_path) as f:
        data = json.load(f)
    assert "team_id" in data
    assert "items" in data
    if expect_items:
        assert isinstance(data["items"], list)
        assert len(data["items"]) > 0
        for item in data["items"]:
            assert "title" in item
            assert "content" in item
            assert "content_type" in item
            assert item["content"]
    os.remove(output_path)

@pytest.mark.parametrize("source", [
    "https://interviewing.io/blog",
    "https://interviewing.io/topics#companies",
    "https://interviewing.io/learn#interview-guides",
    "https://nilmamano.com/blog/category/dsa",
    "https://quill.co/blog"
])
def test_blog_sources(source):
    output = "test_blog.json"
    result = run_cli(source, output=output)
    assert result.returncode == 0
    validate_output(output)

# PDF test is skipped by default (requires manual download)
@pytest.mark.skip(reason="Manual PDF download required for Nil's book.")
def test_pdf_book():
    pdf_path = str(PROJECT_ROOT / "tests/nil_book_sample.pdf")  # Place first 8 chapters here
    output = "test_pdf.json"
    result = run_cli(pdf_path, output=output, force_content_type="book")
    assert result.returncode == 0
    validate_output(output)

@pytest.mark.skip(reason="Google Drive scraping may require authentication or may be rate-limited.")
def test_gdrive_folder():
    source = "https://drive.google.com/drive/folders/1AdUu4jh6DGwmCxfgnDQEMWWyo6_whPHJ"
    output = "test_gdrive.json"
    result = run_cli(source, output=output, force_content_type="book")
    assert result.returncode == 0
    validate_output(output) 