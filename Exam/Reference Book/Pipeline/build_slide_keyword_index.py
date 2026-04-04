"""
Build a clean alphabetical keyword index from the slide title + keyword glossary.

Parses All_Books_Page_Headers_Glossary.txt and produces a clean index:
    term > (B#) page page page, (B#) page page

Only keeps meaningful exam-relevant terms. Aggressively filters noise.
"""

import re
from pathlib import Path
from collections import defaultdict

REF_DIR = Path(r"C:/Users/matth/Downloads/SEC549/Exam/Reference Book")
GLOSSARY_DIR = REF_DIR / "lastminGLossary"
INPUT_FILE = GLOSSARY_DIR / "All_Books_Page_Headers_Glossary.txt"
OUTPUT_FILE = GLOSSARY_DIR / "SEC549_Slide_Keywords_Index.txt"
CLEAN_INDEX_FILE = REF_DIR / "SEC549_Clean_Index.txt"

# ─── Pages to skip entirely (titles that have no exam value) ────────────────
SKIP_TITLE_PATTERNS = [
    r'^table of contents',
    r'^course roadmap',
    r'^course agenda',
    r'^lab \d',
    r'^takeaways',
    r'^section \d',
    r'^introduction to (the |draw)',
    r'^security architecture ahead',
    r'^visualization tools',
]

# ─── Terms to exclude from the final index ──────────────────────────────────
EXCLUDE_TERMS = {
    'warning', 'advantages', 'summary', 'overview', 'approach',
    'cost', 'scalability', 'flexibility', 'performance',
    'os', 'ip', 'ui', 'vm', 'ms', 'ad', 'app', 'api',
    'cots', 'join', 'select', 'cname', 'sha256', 'amqp',
    'ci', 'bq', 'id', 'p005', 'aqab', 'ec2', 'wan',
    'well-architected', 'microsoft', 'google cloud', 'aws', 'azure', 'gcp',
}

# ─── Known acronyms (always keep, display uppercase) ────────────────────────
KNOWN_ACRONYMS = {
    'abac', 'ace', 'acl', 'aks', 'alb', 'arn', 'ava', 'aws',
    'b2b', 'b2c', 'bgp', 'byok',
    'ciam', 'cidr', 'cirt', 'cli', 'cmek', 'cmk', 'cse', 'cspm',
    'dart', 'ddos', 'dlp', 'dns', 'dr',
    'ec2', 'edr', 'eks', 'etl',
    'fido2', 'gcat', 'gcs', 'gke', 'glb',
    'hids', 'hsm', 'https',
    'iam', 'iaas', 'idc', 'idaas', 'idp', 'ids', 'ips',
    'kms',
    'ldap', 'mfa', 'mpls',
    'nacl', 'nat', 'nlb', 'nsg', 'nva',
    'oauth', 'oauth2', 'oidc',
    'paas', 'rbac', 'rpo', 'rto',
    's3', 'saas', 'saml', 'scim', 'scp', 'siem', 'soar', 'soc', 'sso', 'sts',
    'tgw', 'tls',
    'vpc', 'vpn', 'vwan', 'vnet',
    'waf', 'xdr', 'ztna',
}


def is_valid_term(term):
    """Check if a term is valid for the index."""
    lower = term.lower().strip()

    if not lower or len(lower) < 2:
        return False

    if lower in EXCLUDE_TERMS:
        return False

    # Must not start with articles, conjunctions, prepositions
    bad_starts = (
        'the ', 'a ', 'an ', 'and ', 'or ', 'but ', 'in ', 'on ', 'at ',
        'to ', 'for ', 'with ', 'from ', 'by ', 'is ', 'are ', 'was ',
        'of ', 'as ', 'not ', 'if ', 'so ', 'no ', 'its ', 'your ',
        'this ', 'that ', 'these ', 'more ', 'all ',
    )
    if any(lower.startswith(s) for s in bad_starts):
        return False

    # Must not be a sentence fragment (contains common verbs)
    verb_patterns = [
        r'\b(is|are|was|were|has|have|had|does|did|will|can|may|must|should)\b',
        r'\b(using|creating|presented|assigned|established|triggered)\b',
        r'\b(receive|resolve|capture|restrict|evaluate|authorize)\b',
        r'\b(configure|write|produce|consume|assigns|runs|sends)\b',
    ]
    # Only apply verb check to multi-word terms (single known terms are OK)
    if ' ' in lower and len(lower.split()) > 2:
        for vp in verb_patterns:
            if re.search(vp, lower):
                return False

    # Too long = probably a full title or sentence (keep compound terms up to ~6 words)
    if len(lower.split()) > 7:
        return False

    return True


def extract_terms_from_title(title):
    """Extract meaningful compound terms from a slide title.

    From "AWS SCP Goals" → "SCP Goals" (strip cloud provider prefix)
    From "Conditional Access Comparison (1)" → "Conditional Access"
    From "BeyondCorp: Access Context Manager – Basic Policy" →
         "BeyondCorp", "Access Context Manager"
    """
    terms = []

    # Clean numbering like "(1)", "(2)"
    title = re.sub(r'\s*\(\d+\)\s*', '', title).strip()

    # The full title itself (if not too long)
    if len(title.split()) <= 7:
        terms.append(title)

    # Strip cloud provider prefixes and get the core term
    core = re.sub(r'^(?:AWS|Azure|GCP|Google Cloud|Microsoft|Google)\s*:?\s*', '', title).strip()
    if core != title and core:
        terms.append(core)

    # Split on colon or dash separators
    for sep in [':', ' – ', ' - ']:
        if sep in title:
            parts = title.split(sep)
            for p in parts:
                p = p.strip()
                p = re.sub(r'\s*\(\d+\)\s*', '', p).strip()
                if p and len(p) > 3 and len(p.split()) <= 6:
                    terms.append(p)
                    # Also strip provider prefix from sub-parts
                    sub = re.sub(r'^(?:AWS|Azure|GCP|Google Cloud|Microsoft|Google)\s*:?\s*', '', p).strip()
                    if sub != p and sub:
                        terms.append(sub)

    return terms


def normalize_display(term):
    """Normalize a term for display in the index."""
    lower = term.lower().strip()

    # Pure acronyms
    if lower in KNOWN_ACRONYMS:
        return lower.upper()

    # Title case, preserving acronyms
    words = term.split()
    result = []
    for w in words:
        wl = w.lower().strip('()')
        if wl in KNOWN_ACRONYMS:
            # Preserve parentheses if present
            if w.startswith('('):
                result.append('(' + wl.upper() + ')')
            elif w.endswith(')'):
                result.append(wl.upper() + ')')
            else:
                result.append(wl.upper())
        elif w.isupper() and len(w) >= 2:
            result.append(w)  # Keep already-uppercase
        else:
            result.append(w.capitalize() if w[0:1].isalpha() else w)
    return " ".join(result)


def parse_glossary():
    """Parse the glossary file and return {term_lower: {book_num: set(pages)}}."""
    term_index = defaultdict(lambda: defaultdict(set))
    term_display = {}  # term_lower -> best display form

    content = INPUT_FILE.read_text(encoding='utf-8')
    lines = content.split('\n')

    current_book = None
    current_page = None
    skip_page = False

    for line in lines:
        # Detect book header
        m = re.match(r'\s*Book (\d):', line)
        if m:
            current_book = int(m.group(1))
            continue

        # Detect page line
        m = re.match(r'\s*Page\s+(\d+)\s*\|\s*(.+)', line)
        if m:
            current_page = int(m.group(1))
            title_text = m.group(2).strip()

            if current_book is None:
                continue

            # Check if this page should be skipped
            skip_page = False
            for pat in SKIP_TITLE_PATTERNS:
                if re.match(pat, title_text.lower()):
                    skip_page = True
                    break

            if skip_page:
                continue

            # Extract terms from the title
            for term in extract_terms_from_title(title_text):
                term_clean = term.strip()
                if is_valid_term(term_clean):
                    key = term_clean.lower()
                    term_index[key][current_book].add(current_page)
                    # Keep the best display version
                    if key not in term_display:
                        term_display[key] = normalize_display(term_clean)

            continue

        if skip_page:
            continue

        # Detect keyword lines
        m = re.match(r'\s*\|\s*(.+)', line)
        if m and current_book and current_page:
            content_line = m.group(1).strip()

            # Skip separator lines
            if content_line.startswith('+') or content_line.startswith('─'):
                continue

            # Strip "Keywords:" prefix if present
            if content_line.startswith('Keywords:'):
                content_line = content_line[len('Keywords:'):].strip()

            # Parse comma-separated keywords
            keywords = [k.strip() for k in content_line.split(',')]
            for kw in keywords:
                kw = kw.strip(' ,;:()−–—')
                if not kw:
                    continue
                if is_valid_term(kw):
                    key = kw.lower()
                    term_index[key][current_book].add(current_page)
                    if key not in term_display:
                        term_display[key] = normalize_display(kw)

    return term_index, term_display


# ─── Words too generic to be standalone rollup entries ────────────────────────
ROLLUP_STOP_WORDS = {
    # Common English / prepositions / articles / conjunctions
    'the', 'a', 'an', 'and', 'or', 'but', 'in', 'on', 'at', 'to', 'for',
    'with', 'from', 'by', 'of', 'as', 'is', 'are', 'its', 'it', 'be',
    'not', 'no', 'if', 'so', 'all', 'vs', 'how', 'what', 'per', 'via',
    'into', 'than', 'also', 'up', 'out', 'that', 'this', 'more', 'your',
    'between', 'across', 'about', 'over', 'through', 'before', 'after',
    'being', 'does', 'did', 'will', 'can', 'may', 'each', 'both',
    # Generic action/descriptor words (not exam-relevant on their own)
    'common', 'using', 'based', 'putting', 'together', 'define',
    'comparison', 'goals', 'anatomy', 'logic', 'add',
    'within', 'under', 'available', 'simplify', 'view',
    'assign', 'controlling', 'leveraging', 'delegating',
    'recognize', 'failure', 'consider', 'considerations',
    # Cloud providers (already have their own entries via compound terms)
    'aws', 'azure', 'gcp', 'google', 'microsoft',
    # Words user asked to skip
    'lab', 'course', 'roadmap', 'section', 'takeaways',
    # Already excluded at top level
    'warning', 'advantages', 'summary', 'overview', 'approach',
    # Generic verbs / gerunds / adverbs (not useful as standalone lookups)
    'adding', 'additionally', 'addressing', 'allowing', 'allowed',
    'applying', 'architecting', 'assigns', 'authorizing', 'automatically',
    'building', 'communicating', 'consuming', 'denying', 'designing',
    'driven', 'driving', 'enforcing', 'enhancing', 'existing',
    'fully', 'granting', 'identifying', 'long-standing',
    'managed', 'managing', 'manually', 'meeting', 'modernizing',
    'naming', 'needs', 'nesting', 'operating', 'operationalizing',
    'organizing', 'planning', 'processing', 'proposed', 'providing',
    'requiring', 'scaling', 'securing', 'segregating', 'serving',
    'shared', 'sharing', 'starting', 'storing', 'supporting',
    'transitioning', 'understanding', 'unwrapping', 'wrapping',
    # Other generic noise
    'alternate', 'example', 'examples', 'default', 'new', 'full',
    'use', 'cases', 'types', 'type', 'model', 'key',
    'cost', 'scalability', 'flexibility', 'performance',
}


def build_word_rollups(term_index):
    """Extract significant individual words from compound terms and create
    rollup entries that aggregate all pages where that word appears.

    E.g., "roles" will collect pages from "Role Assignments", "Role Bindings",
    "AWS IAM Roles Anywhere", "Role Based Access Control", etc.
    """
    word_index = defaultdict(lambda: defaultdict(set))  # word -> {book: {pages}}

    for term_lower, book_pages in term_index.items():
        # Split compound term into individual words
        words = re.findall(r'[a-z][a-z0-9\-]+', term_lower)
        for word in words:
            # Skip stop words and very short words
            if word in ROLLUP_STOP_WORDS or len(word) < 3:
                continue
            # Skip if it's already an exact entry in term_index
            if word in term_index:
                continue
            # Merge all book/page references
            for book, pages in book_pages.items():
                word_index[word][book].update(pages)

    return word_index


def merge_clean_index_compounds(term_index, term_display):
    """Merge important multi-word compound terms from the Clean Index that are
    missing from the Slide Keyword Index.

    The Clean Index searches ALL body text across the PDFs, so it catches
    compound terms like 'least privilege', 'workload identity federation',
    'defense in depth' that don't appear as slide titles.
    """
    if not CLEAN_INDEX_FILE.exists():
        return 0

    clean_text = CLEAN_INDEX_FILE.read_text(encoding='utf-8')
    junk_chars = set('>{$|~')
    added = 0

    for line in clean_text.split('\n'):
        line = line.rstrip()
        stripped = line.strip()
        if not stripped or not line.startswith('  ') or ' > ' not in stripped:
            continue
        parts = stripped.split(' > ', 1)
        if len(parts) != 2:
            continue
        term, refs_str = parts[0].strip(), parts[1].strip()
        key = term.lower()

        # Only add multi-word terms (single words are handled by rollups)
        if ' ' not in key or len(key) <= 8:
            continue
        # Skip junk / code references
        if any(c in key for c in junk_chars):
            continue
        # Skip if already in the index
        if key in term_index:
            continue
        # Skip generic phrases
        if not is_valid_term(term):
            continue

        # Parse the refs string: "(B1) 42 43, (B2) 10 11"
        book_pages = defaultdict(set)
        for chunk in re.findall(r'\(B(\d)\)\s*([\d\s]+)', refs_str):
            book_num = int(chunk[0])
            pages = {int(p) for p in chunk[1].split()}
            book_pages[book_num].update(pages)

        if book_pages:
            term_index[key] = dict(book_pages)
            term_display[key] = normalize_display(term)
            added += 1

    return added


def format_pages(book_pages):
    """Format {book_num: set(pages)} into '(B1) 5 8 12, (B2) 33 34'."""
    parts = []
    for book in sorted(book_pages.keys()):
        pages = sorted(book_pages[book])
        page_str = " ".join(str(p) for p in pages)
        parts.append(f"(B{book}) {page_str}")
    return ", ".join(parts)


def main():
    print("Parsing glossary...")
    term_index, term_display = parse_glossary()
    print(f"  Found {len(term_index)} unique compound terms")

    # Build single-word rollups from compound terms
    print("Building word rollups...")
    word_rollups = build_word_rollups(term_index)
    # Keep all rollups (even single-page — still useful for exam lookup)
    useful_rollups = {w: bp for w, bp in word_rollups.items()}
    print(f"  Added {len(useful_rollups)} single-word rollup entries")

    # Merge rollups into the main index
    for word, book_pages in useful_rollups.items():
        if word not in term_index:
            term_index[word] = book_pages
            term_display[word] = normalize_display(word)

    # Sort terms alphabetically
    sorted_terms = sorted(term_index.keys())

    # Group by first letter
    letter_groups = defaultdict(list)
    for term in sorted_terms:
        first = term[0].upper() if term[0].isalpha() else '#'
        letter_groups[first].append(term)

    # Write the index
    with open(OUTPUT_FILE, 'w', encoding='utf-8') as f:
        f.write("=" * 80 + "\n")
        f.write("SEC549 SLIDE KEYWORD INDEX -- Extracted from All Page Headers\n")
        f.write("GIAC Exam Reference -- Alphabetical Lookup\n")
        f.write("Format: term > (Book#) page numbers\n")
        f.write("=" * 80 + "\n\n")

        for letter in sorted(letter_groups.keys()):
            f.write(f"-- {letter} " + "-" * 74 + "\n")
            for term_lower in letter_groups[letter]:
                display = term_display.get(term_lower, normalize_display(term_lower))
                pages_str = format_pages(term_index[term_lower])
                f.write(f"  {display} > {pages_str}\n")
            f.write("\n")

    print(f"  Output saved to: {OUTPUT_FILE}")

    # Stats
    total_refs = sum(
        sum(len(pages) for pages in books.values())
        for books in term_index.values()
    )
    print(f"  {len(term_index)} terms, {total_refs} total page references")


if __name__ == "__main__":
    main()
