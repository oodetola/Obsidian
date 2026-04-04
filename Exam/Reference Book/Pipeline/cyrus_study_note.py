"""
Cyrus -- Study Note Generator (v4)
Takes specific index entries (term > book/pages) and extracts ONLY
those pages from the SANS books. No keyword searching — just pulls
the exact pages you specify.

Usage (interactive):
    python cyrus_study_note.py

    Then paste your index entries:
      AWS Cognito > (B2) 78 80
      AWS Cognito Authentication > (B2) 72 75 76 77
      [blank line to finish]

Usage (from file):
    python cyrus_study_note.py --file topics.txt

Usage (single term, falls back to keyword search):
    python cyrus_study_note.py --search "identity pools"
"""

import fitz
import sys
import re
from pathlib import Path
from datetime import datetime
from collections import defaultdict

BOOK_DIR = Path(r"C:/Users/matth/Downloads/SEC549/Exam/tabbed SANS book")
INDEX_FILE = Path(r"C:/Users/matth/Downloads/SEC549/Exam/Reference Book/SEC549_Master_Index.txt")
OUTPUT_DIR = Path(r"C:/Users/matth/Downloads/SEC549/Exam/Reference Book/Study Notes")

BOOK_FILES = {
    1: "SEC549 - Book 1_3355395_Decrypt.pdf",
    2: "SEC549 - Book 2_3355395_Decrypt.pdf",
    3: "SEC549 - Book 3_3355395_Decrypt.pdf",
    4: "SEC549 - Book 4_3355395_Decrypt.pdf",
    5: "SEC549 - Book 5_3355395_Decrypt.pdf",
}

BOOK_TOPICS = {
    1: "Identity & Access Management Foundations",
    2: "Authentication, Federation & Identity Attacks",
    3: "Network Security & Segmentation",
    4: "Cloud Security Governance & Data Protection",
    5: "Detection, Response & Security Operations",
}


def clean_page_text(text):
    """Clean raw PDF page text into readable, properly formatted prose."""
    # Strip watermarks and license junk
    text = re.sub(r'©\s*SANS\s+Institute.*', '', text)
    text = re.sub(r'Licensed To:.*', '', text)
    text = re.sub(r'[a-f0-9]{16,}', '', text)
    text = re.sub(r'<?\S+@\S+\.\S+>?\s*\d*', '', text)
    text = re.sub(r'Olaitan Matthew Odetola', '', text)
    text = re.sub(r'ohNrhAfzA3YUEB7zYQeMv7asRrrC6mmK', '', text)
    text = re.sub(r'\b30531555\b', '', text)
    text = re.sub(r'matthew_odetola@westfraser_com', '', text)
    text = re.sub(r'\n\s*live\s*\n', '\n', text)
    text = re.sub(r'SEC549\s*\|\s*Cloud Security Architecture\s*', '', text)

    # Remove orphan slide page numbers
    text = re.sub(r'^\s*\d{1,3}\s*$', '', text, flags=re.MULTILINE)
    text = re.sub(r'([.!?])\s+\d{1,3}\s+([A-Z])', r'\1 \2', text)
    text = re.sub(r'([.!?])\s+\d{1,3}\s*$', r'\1', text, flags=re.MULTILINE)
    text = re.sub(r'(\w)\d\s+(in |are |is |can |have |enable|allow|do )', r'\1 \2', text)

    # Fix bullet formatting
    text = re.sub(r'[\u2022\u25cf]', '•', text)
    text = re.sub(r'[\u2013\u2212\u2014]', '–', text)
    text = re.sub(r'\s+•\s+', '\n• ', text)
    text = re.sub(r'\s+–\s*(?=[A-Z])', '\n  – ', text)
    text = re.sub(r'\s+−\s*(?=[A-Z])', '\n  – ', text)

    # Strip filler text
    text = re.sub(r'This area is intentionally left blank\.?', '', text)

    # Reflow lines into paragraphs — the key challenge is that PDF extraction
    # splits bullet points and sentences mid-line. We need to rejoin them.
    lines = text.split('\n')
    reflowed = []

    def _is_new_block(s):
        """Does this line start a new logical block (not a continuation)?"""
        if not s:
            return True
        if s.startswith('•') or s.startswith('–') or s.startswith('- '):
            return True
        if re.match(r'^\d+[\.\)]\s', s):
            return True
        if s.startswith('http') or s.lower().startswith('references:'):
            return True
        return False

    def _is_heading(s):
        """Is this a short title-case heading?"""
        if not s or len(s) >= 100 or s.endswith('.') or s.endswith(','):
            return False
        if not s[0].isupper():
            return False
        words = s.split()
        if len(words) < 2 or len(words) > 15:
            return False
        caps = sum(1 for w in words if w[0:1].isupper())
        return caps >= len(words) * 0.6

    for line in lines:
        stripped = line.strip()
        if not stripped:
            reflowed.append('')
            continue

        # New block starters always get their own line
        if _is_new_block(stripped):
            reflowed.append(stripped)
            continue

        # If previous line exists, decide: join as continuation or start new
        if reflowed and reflowed[-1]:
            prev = reflowed[-1]
            prev_ends_sentence = prev.endswith(('.', '!', '?', ':'))

            # Previous line is a bullet/sub-bullet that doesn't end a sentence?
            # This line is a continuation of that bullet.
            if ((prev.startswith('•') or prev.startswith('–'))
                    and not prev_ends_sentence):
                reflowed[-1] = prev + ' ' + stripped
                continue

            # Previous line is a numbered step that doesn't end a sentence?
            if re.match(r'^\d+[\.\)]', prev) and not prev_ends_sentence:
                reflowed[-1] = prev + ' ' + stripped
                continue

            # Previous line is regular text that doesn't end a sentence?
            if not prev_ends_sentence:
                reflowed[-1] = prev + ' ' + stripped
                continue

            # Previous line ends a sentence — is this a heading or new paragraph?
            if _is_heading(stripped):
                reflowed.append(stripped)
                continue

            # Otherwise start a new paragraph
            reflowed.append(stripped)
        else:
            reflowed.append(stripped)

    text = '\n'.join(reflowed)
    text = re.sub(r'[ \t]+', ' ', text)
    text = re.sub(r'\n{3,}', '\n\n', text)
    return text.strip()


def parse_index_entries(lines):
    """
    Parse index entries like:
      AWS Cognito > (B2) 78 80
      AWS Cognito Authentication > (B2) 72 75 76 77
    Returns: list of (term, {book: [pages]})
    """
    entries = []
    for line in lines:
        line = line.strip()
        if not line or line.startswith('#') or line.startswith('--'):
            continue
        m = re.match(r'^(.+?)\s*>\s*(.+)$', line)
        if not m:
            continue
        term = m.group(1).strip()
        refs_str = m.group(2).strip()
        book_pages = {}
        for part in re.split(r',\s*', refs_str):
            bm = re.match(r'\(B(\d)\)\s*([\d\s]+)', part.strip())
            if bm:
                book = int(bm.group(1))
                pages = [int(p) for p in bm.group(2).split()]
                book_pages[book] = pages
        if book_pages:
            entries.append((term, book_pages))
    return entries


def extract_pages(entries):
    """
    Given parsed entries, collect unique (book, page) pairs,
    extract full cleaned text from each page.
    Returns: {book: {page: cleaned_text}}
    """
    # Collect all unique pages needed per book
    needed = defaultdict(set)
    for term, book_pages in entries:
        for book, pages in book_pages.items():
            needed[book].update(pages)

    extracted = defaultdict(dict)
    for book_num in sorted(needed.keys()):
        filename = BOOK_FILES.get(book_num)
        if not filename:
            continue
        filepath = BOOK_DIR / filename
        if not filepath.exists():
            print(f"  WARNING: {filepath.name} not found")
            continue

        pages_needed = sorted(needed[book_num])
        doc = fitz.open(str(filepath))
        print(f"  Book {book_num}: extracting pages {', '.join(str(p) for p in pages_needed)}")
        for page_num in pages_needed:
            if page_num - 1 < doc.page_count:
                raw = doc[page_num - 1].get_text()
                extracted[book_num][page_num] = clean_page_text(raw)
        doc.close()

    return extracted


def generate_study_note(title, entries, extracted):
    """Generate a focused .md study note from the extracted pages."""
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    safe_name = re.sub(r'[^\w\s-]', '', title).strip().replace(' ', '_')
    safe_name = safe_name[:60]
    filename = f"StudyNote_{safe_name}.md"
    outpath = OUTPUT_DIR / filename

    # Build ordered list of (book, page, [terms that reference this page])
    page_terms = defaultdict(list)
    all_books = set()
    for term, book_pages in entries:
        for book, pages in book_pages.items():
            all_books.add(book)
            for page in pages:
                page_terms[(book, page)].append(term)

    # Deduplicate pages, sort by book then page
    all_pages = sorted(page_terms.keys())
    total_pages = len(all_pages)

    with open(outpath, 'w', encoding='utf-8') as f:
        # Header
        f.write(f"# {title}\n\n")
        f.write(f"Generated: {datetime.now().strftime('%Y-%m-%d')} | ")
        f.write(f"{total_pages} pages from {len(all_books)} book(s)\n\n")

        # Flip table
        f.write("---\n\n")
        f.write("## Flip To These Pages\n\n")
        f.write("| Book | Pages | Domain |\n")
        f.write("|------|-------|--------|\n")
        for book_num in sorted(all_books):
            book_pages = sorted(p for b, p in all_pages if b == book_num)
            page_list = ', '.join(str(p) for p in book_pages)
            topic = BOOK_TOPICS.get(book_num, '')
            f.write(f"| **(B{book_num})** | **{page_list}** | {topic} |\n")
        f.write("\n")

        # Index entries used
        f.write("**Topics covered:**\n\n")
        for term, book_pages in entries:
            refs = ', '.join(
                f"(B{b}) {' '.join(str(p) for p in pgs)}"
                for b, pgs in sorted(book_pages.items())
            )
            f.write(f"- `{term}` > {refs}\n")
        f.write("\n---\n\n")

        # Page content organized by book
        for book_num in sorted(all_books):
            f.write(f"## Book {book_num} -- {BOOK_TOPICS.get(book_num, '')}\n\n")

            book_page_list = sorted(p for b, p in all_pages if b == book_num)
            for page_num in book_page_list:
                terms = page_terms[(book_num, page_num)]
                terms_label = ' | '.join(terms)
                f.write(f"### (B{book_num}) p.{page_num} -- {terms_label}\n\n")

                text = extracted.get(book_num, {}).get(page_num, '')
                if not text:
                    f.write("> _(Page content not available)_\n\n")
                    continue

                # Split into paragraphs and format as blockquotes
                paragraphs = re.split(r'\n\n+', text)
                for para in paragraphs:
                    para = para.strip()
                    if not para or len(para) < 10:
                        continue
                    lines = para.split('\n')
                    for line in lines:
                        line = line.rstrip()
                        if line:
                            f.write(f"> {line}\n")
                        else:
                            f.write(">\n")
                    f.write("\n")

            f.write("---\n\n")

        # Review checklist
        f.write("## Review Checklist\n\n")
        for term, _ in entries:
            f.write(f"- [ ] {term}\n")

    return outpath


def main():
    # Determine mode
    if len(sys.argv) > 1 and sys.argv[1] == '--search':
        # Legacy keyword search mode
        keyword = sys.argv[2] if len(sys.argv) > 2 else ''
        if not keyword:
            print("Usage: python cyrus_study_note.py --search \"keyword\"")
            sys.exit(1)
        # Look up in index and convert to entries
        keyword_lower = keyword.lower().strip()
        index_text = INDEX_FILE.read_text(encoding='utf-8')
        raw_lines = []
        for line in index_text.split('\n'):
            line = line.strip()
            if ' > ' in line:
                term = line.split(' > ', 1)[0].strip()
                if keyword_lower == term.lower():
                    raw_lines.append(line)
        if not raw_lines:
            print(f"No exact index match for \"{keyword}\"")
            sys.exit(1)
        entries = parse_index_entries(raw_lines)
        note_title = keyword.strip()

    elif len(sys.argv) > 1 and sys.argv[1] == '--file':
        # File input mode
        fpath = Path(sys.argv[2]) if len(sys.argv) > 2 else None
        if not fpath or not fpath.exists():
            print("Usage: python cyrus_study_note.py --file topics.txt")
            sys.exit(1)
        raw_lines = fpath.read_text(encoding='utf-8').split('\n')
        entries = parse_index_entries(raw_lines)
        note_title = fpath.stem.replace('_', ' ').title()

    else:
        # Interactive / stdin mode
        print(f"\n{'='*60}")
        print(f"  STUDY NOTE GENERATOR")
        print(f"  Paste your index entries, then press Enter twice:")
        print(f"{'='*60}\n")
        raw_lines = []
        while True:
            try:
                line = input()
            except EOFError:
                break
            if not line.strip():
                break
            raw_lines.append(line)

        if not raw_lines:
            print("No entries provided.")
            sys.exit(1)

        entries = parse_index_entries(raw_lines)
        # Derive title from the shortest/broadest term
        if entries:
            terms_sorted = sorted(entries, key=lambda e: len(e[0]))
            note_title = terms_sorted[0][0]

    if not entries:
        print("Could not parse any valid entries.")
        sys.exit(1)

    print(f"\n{'='*60}")
    print(f"  Title: {note_title}")
    print(f"  Entries: {len(entries)}")
    unique_pages = set()
    for _, bp in entries:
        for b, pgs in bp.items():
            for p in pgs:
                unique_pages.add((b, p))
    print(f"  Unique pages to extract: {len(unique_pages)}")
    print(f"{'='*60}\n")

    print("Extracting pages from SANS books...")
    extracted = extract_pages(entries)

    print(f"\nGenerating study note...")
    outpath = generate_study_note(note_title, entries, extracted)
    print(f"  Saved: {outpath}")

    print(f"\n{'='*60}")
    print(f"  DONE")
    print(f"{'='*60}")


if __name__ == '__main__':
    main()
