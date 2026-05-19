import trafilatura
import json
from datetime import datetime, timezone
from pathlib import Path
import httpx

# Paths

DATA_DIR = Path("data")
OUTPUT_FILE_LIVE = DATA_DIR / "crawler_output_live.jsonl"
OUTPUT_FILE_LOCAL = DATA_DIR / "crawler_output_local.jsonl"


# 7 TARGET URLS (Live mode - only executed once to prevent antiparsing bot)

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

# Helper functions

def fetch_html_from_web(url):
    print(f"Fetching: {url}")
    response = httpx.get(url, timeout=15)
    response.raise_for_status()
    return response.text

def load_html_from_file(path):
    print(f"Loading local file: {path.name}")
    return path.read_text(encoding="utf-8")

def extract_clean_text(html):
    return trafilatura.extract(
        html,
        include_comments=False,
        include_tables=False
    )

def is_useful(text, min_words=500):
    return text is not None and len(text.split()) >= min_words

def process_html(html, source, file_name, url=None):
    clean_text = extract_clean_text(html)

    if not is_useful(clean_text):
        print(f"Rejected {file_name} (insufficient content)")
        return None

    return {
        "source": source,
        "url": url,
        "file": file_name,
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "word_count": len(clean_text.split()),
        "text": clean_text
    }

# Main

def main():
    print("Select data source:")
    print("1 - Fetch ALL 7 pages from the web (RUN ONCE ONLY)")
    print("2 - Use local saved HTML files")

    choice = input("Your choice (1 or 2): ").strip()
    output_file = (
    OUTPUT_FILE_LIVE if choice == "1" else OUTPUT_FILE_LOCAL
    )

    records = []

    # Live fetch mode

    if choice == "1":
        for page in TARGET_PAGES:
            try:
                html = fetch_html_from_web(page["url"])
            except Exception as e:
                print(f"Skipping {page['url']} ({e})")
                continue

            html_path = DATA_DIR / page["file"]
            html_path.write_text(html, encoding="utf-8")

            record = process_html(
                html=html,
                source="live_fetch",
                file_name=page["file"],
                url=page["url"]
            )

            if record:
                records.append(record)

    # Local mode 

    elif choice == "2":
        for page in TARGET_PAGES:
            html_path = DATA_DIR / page["file"]

            if not html_path.exists():
                print(f"Missing file: {html_path.name}")
                continue

            html = load_html_from_file(html_path)

            record = process_html(
                html=html,
                source="local_html",
                file_name=html_path.name
            )

            if record:
                records.append(record)

    else:
        print("Invalid choice.")
        return

    if not records:
        print("No valid pages extracted.")
        return

    with open(output_file, "w", encoding="utf-8") as f:
        for r in records:
            f.write(json.dumps(r, ensure_ascii=False) + "\n")

    print(f"Extraction complete: {len(records)} pages saved to {output_file.name}")

if __name__ == "__main__":
    main()
