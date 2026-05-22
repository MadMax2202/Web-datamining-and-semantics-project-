"""
crawl_and_clean.py

This script performs the data acquisition and cleaning step of the project.

It starts from a small set of manually selected seed URLs in the bench press /
strength training domain. The script can either fetch the pages live from the web
or reuse locally saved HTML files. Live fetching should only be done once, because
the HTML is saved locally for reproducibility and to avoid repeatedly requesting
the same websites.

For each page, the script:
1. Downloads or loads the HTML.
2. Extracts the main readable text with Trafilatura.
3. Removes pages with insufficient useful text.
4. Stores metadata such as URL, source mode, timestamp, word count, and text hash.
5. Saves the cleaned documents into a JSONL file.

The output JSONL file is then used by extract_entities.py for information
extraction and knowledge-base construction.
"""

import json
import time
import hashlib
from datetime import datetime, timezone
from pathlib import Path

import httpx
import trafilatura


# =============================
# PATHS
# =============================

PROJECT_ROOT = Path(__file__).resolve().parents[1]

HTML_DIR = PROJECT_ROOT / "01_Data" / "html_files"
OUTPUT_DIR = PROJECT_ROOT / "01_Data" / "crawler_outputs"

OUTPUT_FILE_LIVE = OUTPUT_DIR / "crawler_output_live.jsonl"
OUTPUT_FILE_LOCAL = OUTPUT_DIR / "crawler_output_local.jsonl"


# =============================
# ETHICAL CRAWLING SETTINGS
# =============================

REQUEST_DELAY_SECONDS = 2

USER_AGENT = (
    "WebDataminingStudentBot/1.0 "
    "(educational project; controlled seed URL crawl)"
)


# =============================
# SEED URLS
# =============================

TARGET_PAGES = [
    {
        "url": "https://www.nike.com/a/how-and-why-to-do-a-bench-press",
        "file": "Nike_bench_press.html"
    },
    {
        "url": "https://www.muscleandmotion.com/how-to-bench-press-properly/",
        "file": "muscleandmotion_bench_press.html"
    },
    {
        "url": "https://blog.nasm.org/biomechanics-of-the-bench-press",
        "file": "nasm_bench_press.html"
    },
    {
        "url": "https://www.frontiersin.org/journals/sports-and-active-living/articles/10.3389/fspor.2020.637066/full",
        "file": "frontiersin_bench_press.html"
    },
    {
        "url": "https://robertsontrainingsystems.com/blog/biomechanics-and-the-bench-press/",
        "file": "robertson_bench_press.html"
    },
    {
        "url": "https://www.strongerbyscience.com/how-to-bench/",
        "file": "strongerbyscience_bench_press.html"
    },
    {
        "url": "https://www.mdpi.com/2076-3417/14/24/11783",
        "file": "mdpi_bench_press.html"
    }
]


# =============================
# HELPER FUNCTIONS
# =============================

def fetch_html_from_web(url: str) -> tuple[str, int, str]:
    """
    Fetch one HTML page from the web using a custom User-Agent and a delay.

    The delay and local caching strategy are used to avoid aggressive crawling.
    """
    print(f"Fetching: {url}")

    headers = {
        "User-Agent": USER_AGENT
    }

    response = httpx.get(
        url,
        timeout=20,
        headers=headers,
        follow_redirects=True
    )

    response.raise_for_status()

    content_type = response.headers.get("content-type", "")

    if "text/html" not in content_type.lower():
        raise ValueError(f"Non-HTML content skipped: {content_type}")

    time.sleep(REQUEST_DELAY_SECONDS)

    return response.text, response.status_code, content_type


def load_html_from_file(path: Path) -> str:
    """
    Load previously saved HTML from the local data folder.
    """
    print(f"Loading local file: {path.name}")
    return path.read_text(encoding="utf-8")


def extract_clean_text(html: str) -> str | None:
    """
    Extract the main article text from raw HTML.

    Trafilatura removes most boilerplate such as navigation menus, scripts,
    style tags, comments, and irrelevant page structure.
    """
    return trafilatura.extract(
        html,
        include_comments=False,
        include_tables=False,
        favor_recall=True
    )


def is_useful(text: str | None, min_words: int = 500) -> bool:
    """
    Keep only pages with enough extracted text to be useful for IE.
    """
    return text is not None and len(text.split()) >= min_words


def compute_text_hash(text: str) -> str:
    """
    Compute a SHA-256 hash of the cleaned text for duplicate detection.
    """
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def process_html(
    html: str,
    source: str,
    file_name: str,
    url: str | None = None,
    status_code: int | None = None,
    content_type: str | None = None
) -> dict | None:
    """
    Convert raw HTML into one cleaned JSONL-ready record.
    """
    clean_text = extract_clean_text(html)

    if not is_useful(clean_text):
        print(f"Rejected {file_name} because extracted text was too short.")
        return None

    clean_text = clean_text.strip()

    return {
        "source": source,
        "url": url,
        "file": file_name,
        "timestamp_utc": datetime.now(timezone.utc).isoformat(),
        "status_code": status_code,
        "content_type": content_type,
        "word_count": len(clean_text.split()),
        "text_hash": compute_text_hash(clean_text),
        "text": clean_text
    }


def deduplicate_records(records: list[dict]) -> list[dict]:
    """
    Remove duplicate pages based on the hash of their cleaned text.
    """
    unique_records = []
    seen_hashes = set()

    for record in records:
        text_hash = record["text_hash"]

        if text_hash in seen_hashes:
            print(f"Duplicate skipped: {record['file']}")
            continue

        seen_hashes.add(text_hash)
        unique_records.append(record)

    return unique_records


def save_jsonl(records: list[dict], output_file: Path) -> None:
    """
    Save cleaned records as JSON Lines.
    """
    with open(output_file, "w", encoding="utf-8") as f:
        for record in records:
            f.write(json.dumps(record, ensure_ascii=False) + "\n")


# =============================
# MAIN
# =============================

def main() -> None:
    HTML_DIR.mkdir(parents=True, exist_ok=True)
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    print("Select data source:")
    print("1 - Fetch ALL seed pages from the web")
    print("2 - Use local saved HTML files")
    print()
    print("Recommended workflow:")
    print("- Run option 1 only once.")
    print("- Then use option 2 for reproducible local experiments.")
    print()

    choice = input("Your choice (1 or 2): ").strip()

    if choice == "1":
        output_file = OUTPUT_FILE_LIVE
    elif choice == "2":
        output_file = OUTPUT_FILE_LOCAL
    else:
        print("Invalid choice. Please choose 1 or 2.")
        return

    records = []

    if choice == "1":
        print("\nRunning in LIVE FETCH mode.\n")

        for page in TARGET_PAGES:
            url = page["url"]
            html_file = HTML_DIR / page["file"]

            try:
                html, status_code, content_type = fetch_html_from_web(url)
            except Exception as e:
                print(f"Skipping {url} because of error: {e}")
                continue

            html_file.write_text(html, encoding="utf-8")
            print(f"Saved raw HTML to: {html_file}")

            record = process_html(
                html=html,
                source="live_fetch",
                file_name=page["file"],
                url=url,
                status_code=status_code,
                content_type=content_type
            )

            if record:
                records.append(record)

    elif choice == "2":
        print("\nRunning in LOCAL HTML mode.\n")

        for page in TARGET_PAGES:
            html_path = HTML_DIR / page["file"]

            if not html_path.exists():
                print(f"Missing local file: {html_path.name}")
                continue

            html = load_html_from_file(html_path)

            record = process_html(
                html=html,
                source="local_html",
                file_name=html_path.name,
                url=page["url"]
            )

            if record:
                records.append(record)

    if not records:
        print("No valid pages extracted.")
        return

    records = deduplicate_records(records)
    save_jsonl(records, output_file)

    print()
    print("Extraction complete.")
    print(f"Valid cleaned pages: {len(records)}")
    print(f"Saved to: {output_file}")


if __name__ == "__main__":
    main()