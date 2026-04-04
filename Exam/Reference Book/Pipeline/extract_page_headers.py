"""
Extract the slide title + keywords from every page across all 5 SEC549 SANS books.

SANS slide PDF layout (US Letter 612x792pt):
  y ≈ 37       Course title "SEC549 | Cloud Security Architecture" (6.4pt, skip)
  y ≈ 45       Watermark / © SANS (35pt, skip)
  y ≈ 50-94    SLIDE TITLE (13.9pt or 18.5pt) ← extract
  y ≈ 96-350   SLIDE BODY: sub-headers, bullet points, keywords ← extract keywords
  y ≈ 370+     NOTES SECTION (12.6pt paragraph text) ← skip

This script extracts the title and then mines the slide body for useful
keywords: sub-headers, technical terms, acronyms, and service names.
"""

import sys
import io
import re
from pathlib import Path
from collections import OrderedDict

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')

import fitz  # PyMuPDF

BOOKS_DIR = Path(r"C:/Users/matth/Downloads/SEC549/Exam/tabbed SANS book")
OUTPUT_DIR = Path(r"C:/Users/matth/Downloads/SEC549/Exam/Reference Book/lastminGLossary")

BOOK_FILES = [
    ("Book 1", "SEC549 - Book 1_3355395_Decrypt.pdf", "Cloud Account Management and Identity Foundations"),
    ("Book 2", "SEC549 - Book 2_3355395_Decrypt.pdf", "Implementing Zero Trust Architecture"),
    ("Book 3", "SEC549 - Book 3_3355395_Decrypt.pdf", "Network Access Perimeters"),
    ("Book 4", "SEC549 - Book 4_3355395_Decrypt.pdf", "Data Access Perimeters"),
    ("Book 5", "SEC549 - Book 5_3355395_Decrypt.pdf", "Security Operations and Incident Response"),
]

SKIP_PAGES = {
    "Book 1": [0, 1, 2],
    "Book 2": [0, 1, 2],
    "Book 3": [0, 1, 2],
    "Book 4": [0, 1, 2],
    "Book 5": [0, 1, 2],
}

# ─── Known technical terms / service names to always capture ────────────────
KNOWN_TERMS = {
    # Cloud providers & core services
    "AWS", "Azure", "GCP", "Google Cloud", "Microsoft",
    # Identity
    "IAM", "RBAC", "ABAC", "SAML", "OIDC", "OAuth2", "OAuth", "MFA", "SSO",
    "SCIM", "LDAP", "Kerberos", "FIDO2",
    "Entra ID", "Entra", "Okta", "Auth0", "Cognito", "PingIdentity",
    "Active Directory", "Azure AD",
    "Identity Center", "IdC", "IdP", "CSP",
    "SCP", "STS", "ARN",
    # Zero Trust
    "Zero Trust", "BeyondCorp", "BeyondProd", "ZTNA",
    "PagerDuty", "Verified Access", "AVA",
    # Network
    "VPC", "VNet", "VWAN", "VPN", "NAT", "DNS", "BGP",
    "CIDR", "ACL", "NACL", "NVA",
    "Transit Gateway", "TGW", "VPC Peering",
    "PrivateLink", "Private Endpoint", "Service Endpoint",
    "Route 53", "Cloud DNS", "Azure DNS",
    "NSG", "Security Group", "Firewall",
    "Load Balancer", "ALB", "NLB", "GLB",
    "WAF", "DDoS", "Cloud Armor", "AWS Shield",
    "ExpressRoute", "Direct Connect", "Cloud Interconnect",
    # Data
    "KMS", "HSM", "CMK", "CMEK", "SSE", "CSE",
    "S3", "Blob Storage", "Cloud Storage", "GCS",
    "DLP", "Macie", "Purview",
    "Encryption", "Envelope Encryption",
    # Logging & Security Ops
    "CloudTrail", "CloudWatch", "Activity Log", "Audit Log",
    "Flow Logs", "VPC Flow Logs",
    "GuardDuty", "Security Hub", "Sentinel", "Chronicle",
    "SIEM", "SOAR", "SOC", "XDR",
    "EventBridge", "Event Grid", "Pub/Sub",
    "Cribl", "Splunk", "Kinesis",
    # Containers & Compute
    "Kubernetes", "K8s", "EKS", "AKS", "GKE",
    "Lambda", "Cloud Functions", "Cloud Run",
    "Docker", "Container", "Pod",
    # Frameworks & Methodologies
    "STRIDE", "DREAD", "LINDDUN", "MITRE", "NIST",
    "CIS", "SABSA", "Well-Architected",
    "OWASP", "CVE", "CVSS",
    # DR
    "DR", "RPO", "RTO", "Backup",
}

# Patterns to skip entirely
SKIP_PATTERNS = [
    re.compile(r'[0-9a-f]{6,}', re.IGNORECASE),   # Hex watermarks
    re.compile(r'©\s*SANS', re.IGNORECASE),        # Copyright
    re.compile(r'^SEC549\s*\|?\s*Cloud', re.IGNORECASE),  # Course title
    re.compile(r'^Licensed To:', re.IGNORECASE),    # License watermark
]

# Common filler words to strip from keyword candidates
FILLER_WORDS = {
    'the', 'a', 'an', 'is', 'are', 'was', 'were', 'be', 'been', 'being',
    'have', 'has', 'had', 'do', 'does', 'did', 'will', 'would', 'could',
    'should', 'may', 'might', 'shall', 'can', 'must', 'need', 'dare',
    'to', 'of', 'in', 'for', 'on', 'with', 'at', 'by', 'from', 'as',
    'into', 'through', 'during', 'before', 'after', 'above', 'below',
    'between', 'under', 'over', 'out', 'up', 'down', 'off', 'about',
    'and', 'but', 'or', 'nor', 'not', 'so', 'yet', 'both', 'either',
    'neither', 'each', 'every', 'all', 'any', 'few', 'more', 'most',
    'other', 'some', 'such', 'no', 'only', 'same', 'than', 'too',
    'very', 'just', 'also', 'now', 'here', 'there', 'when', 'where',
    'how', 'what', 'which', 'who', 'whom', 'this', 'that', 'these',
    'those', 'it', 'its', 'you', 'your', 'we', 'our', 'they', 'their',
    'i', 'me', 'my', 'he', 'she', 'him', 'her', 'us', 'them',
}


def should_skip_span(text):
    """Check if a text span should be completely skipped."""
    for pattern in SKIP_PATTERNS:
        if pattern.search(text):
            return True
    return False


def group_spans_to_lines(spans, split_columns=False):
    """Group text spans into lines by y-position proximity.

    If split_columns=True, also split lines when there's a large x-gap
    (> 100pt) indicating multi-column layout.
    """
    if not spans:
        return []
    spans.sort(key=lambda s: (s[0], s[2]))  # Sort by y, then x
    lines = []
    current_parts = []  # list of (x, text)
    current_y = None

    for y, sz, x, text in spans:
        if current_y is None or abs(y - current_y) < 4:
            current_parts.append((x, text))
            current_y = y if current_y is None else current_y
        else:
            # Flush current line
            _flush_line(current_parts, lines, split_columns)
            current_parts = [(x, text)]
            current_y = y
    if current_parts:
        _flush_line(current_parts, lines, split_columns)
    return lines


def _flush_line(parts, lines, split_columns):
    """Flush accumulated parts into one or more lines."""
    if not parts:
        return
    parts.sort(key=lambda p: p[0])  # Sort by x-position

    if split_columns and len(parts) > 1:
        # Check for large x-gaps indicating column breaks
        groups = [[parts[0]]]
        for i in range(1, len(parts)):
            x_gap = parts[i][0] - (parts[i-1][0] + len(parts[i-1][1]) * 5)
            if x_gap > 80:  # Large gap = new column
                groups.append([parts[i]])
            else:
                groups[-1].append(parts[i])
        for group in groups:
            combined = " ".join(t for _, t in group).strip()
            if combined:
                lines.append(combined)
    else:
        combined = " ".join(t for _, t in parts).strip()
        if combined:
            lines.append(combined)


def is_subheader(text):
    """Check if a short text line is a sub-header/label (not a sentence fragment).

    Good sub-headers: "Workforce IAM", "Cost", "Policy-centric security",
                      "Single Sign-On (SSO)", "AWS Well-Architected Framework"
    Bad (sentence fragments): "Apple's failure to fully threat model",
                              "Security design must recognize the",
                              "Architectural complexity arises because"
    """
    if not text or len(text) < 3 or len(text) > 45:
        return False
    if not text[0].isupper():
        return False

    lower = text.lower()
    words = lower.split()

    # Skip if starts with common sentence-starting words
    sentence_starters = {
        'the', 'a', 'an', 'this', 'that', 'these', 'those', 'it', 'its',
        'when', 'where', 'how', 'what', 'which', 'who', 'also', 'once',
        'if', 'in', 'on', 'at', 'for', 'with', 'from', 'to', 'be',
        'have', 'often', 'without', 'you', 'we', 'they', 'there',
        'some', 'each', 'only', 'both', 'such', 'may', 'must',
        'should', 'can', 'will', 'would', 'could', 'does', 'did',
        'not', 'no', 'or', 'but', 'and', 'so', 'yet',
        'welcome', 'groups', 'modeling', 'finding', 'document',
        'democratize', 'reviewed', 'configured', 'explored',
    }
    if words and words[0] in sentence_starters:
        return False

    # Skip if contains common verb patterns (sign of sentence fragment)
    verb_patterns = [
        r'\b(arises?|defines?|recognizes?|applies?|ensures?|addresses?)\b',
        r'\b(requires?|provides?|enables?|allows?|supports?|involves?)\b',
        r'\b(uses?|manages?|handles?|controls?|creates?|focuses)\b',
        r"\b(failure|failures|is concerned|is defined|is made)\b",
        r"\b('s failure|'s \w+ to)\b",
        r'\b(should be|must be|can be|will be|are often|are used)\b',
        r'\b(leads? to|designed for|goes beyond|play it|will address)\b',
        r'\b(complex systems|multinational|cross-functional|identified)\b',
        r'\b(Welcome to|Reviewed |Configured |Explored |Tested )\b',
        r'\bare\s+\w+ed\b',                    # "are presented", "are evaluated"
        r'\bare\s+\w+ing\b',                   # "are managing"
        r'\b(is an?|is the|are the)\b',         # "is a", "is an", "is the"
        r'\bagainst\b',                          # "against an external"
        r'\bdon\'t\b',                           # contractions = sentence
        r'\bcan\'t\b',
        r'\bestablished with\b',
        r'\bconnect to\b',
        r'\busers? (are|managed|presented)\b',   # "users are presented"
        r'\brestrict\b',                         # "restrict BigQuery"
        r'\bevaluates?\b',                       # "evaluates the"
        r'\bauthorizes?\b',                      # "authorizes"
        r'\bruns? a\b',                          # "runs a"
        r'\bwrites?\b',                          # "write"
    ]
    for vp in verb_patterns:
        if re.search(vp, lower):
            return False

    # Skip endings that indicate sentences
    if text.endswith('.') or text.endswith(':') or text.endswith(';'):
        return False

    # More than 5 words - probably a sentence unless it's all capitalized terms
    if len(words) > 5:
        return False

    # Skip generic/filler
    skip_exact = {
        'takeaways', 'course roadmap', 'summary', 'in this lab, you',
        'references', 'reference', 'management', 'foundations', 'course',
        'agenda', 'warning', 'examples include', 'perimeter in the cloud',
    }
    if lower.strip(',: ') in skip_exact:
        return False

    # Skip section title patterns
    if re.match(r'^section \d', lower):
        return False

    return True


def extract_keywords_from_text(subheader_lines, regular_lines, title_text):
    """Extract useful keywords from slide body text.

    Args:
        subheader_lines: Lines from large-font text (13.9pt) - these are sub-headers/labels
        regular_lines: Lines from smaller-font text (11-12.7pt) - bullet point content
        title_text: The slide title (for dedup)

    Strategy:
    1. Sub-headers (13.9pt) are treated as label keywords directly
    2. Regular text is mined for known terms, acronyms, and parenthetical definitions
    """
    keywords = OrderedDict()
    title_lower = title_text.lower()
    all_text = " ".join(subheader_lines + regular_lines)

    # 1. Sub-headers from 13.9pt text - these ARE the labels/keywords
    for line in subheader_lines:
        cleaned = re.sub(r'^[\u2022\u2212\u2013\u2014\-•]+\s*', '', line).strip()
        cleaned = cleaned.rstrip(',;')
        if not cleaned or len(cleaned) < 3:
            continue
        # Sub-headers should look like labels, not sentence fragments
        # Extra check: if it ends with a preposition/article, it's a sentence fragment
        if not is_subheader(cleaned):
            continue
        if cleaned.lower() not in title_lower:
            # Skip fragments ending with connectors/prepositions
            trail = cleaned.split()[-1].lower() if cleaned.split() else ''
            if trail in ('and', 'or', 'the', 'a', 'an', 'is', 'are', 'to',
                         'in', 'of', 'for', 'with', 'from', 'by', 'at', 'on',
                         'that', 'this', 'your', 'their', 'its', 'our'):
                continue
            keywords[cleaned] = True

    # 2. Known technical terms (search in ALL text)
    for term in KNOWN_TERMS:
        pattern = r'\b' + re.escape(term) + r'\b'
        if re.search(pattern, all_text, re.IGNORECASE):
            if term.lower() not in title_lower:
                keywords[term] = True

    # 3. Acronyms from ALL text
    SKIP_ACRONYMS = {
        'IN', 'OR', 'TO', 'IF', 'IS', 'IT', 'ON', 'AT', 'OF', 'BY',
        'AN', 'AS', 'SO', 'NO', 'DO', 'UP', 'US', 'WE', 'BE', 'HE',
        'ME', 'MY', 'ID', 'AM', 'PM', 'VS', 'II', 'RE', 'RS', 'OK',
        'OU', 'DC', 'UK', 'EU', 'THE', 'AND', 'FOR', 'ARE', 'BUT',
        'NOT', 'YOU', 'ALL', 'CAN', 'HER', 'WAS', 'ONE', 'OUR',
    }
    acronyms = set(re.findall(r'\b([A-Z][A-Z0-9]{1,10})\b', all_text))
    for acr in sorted(acronyms):
        if acr not in SKIP_ACRONYMS and acr.lower() not in title_lower:
            keywords[acr] = True

    # 4. Parenthetical definitions from ALL text - "(ACE)", "(CIAM)", "(IdC)"
    parens = re.findall(r'\(([A-Za-z][A-Za-z0-9\s\-/]{0,20})\)', all_text)
    for p in parens:
        p = p.strip()
        if (p and 2 <= len(p) <= 20
                and p.lower() not in FILLER_WORDS
                and p.lower() not in title_lower):
            keywords[p] = True

    # Cleanup
    final = []
    seen_lower = set()
    for kw in keywords:
        kw_clean = kw.strip(' ,;:()')
        if not kw_clean or len(kw_clean) < 2:
            continue
        kw_lower = kw_clean.lower()
        if kw_lower in seen_lower:
            continue
        if ' ' not in kw_clean and kw_clean.lower() in FILLER_WORDS:
            continue
        seen_lower.add(kw_lower)
        final.append(kw_clean)

    return final


def extract_page_data(page, page_num):
    """Extract slide title and keywords from a single page.

    Returns: (title_lines, keywords) or None
    """
    blocks = page.get_text("dict")
    if not blocks or "blocks" not in blocks:
        return None

    title_spans = []   # y=50-95, sz≥13.5 (slide title)
    body_spans = []    # y=96-355, sz≥11 (slide body, not notes)

    for block in blocks["blocks"]:
        if block["type"] != 0:
            continue
        for line_data in block["lines"]:
            for span in line_data["spans"]:
                text = span["text"].strip()
                sz = span["size"]
                y = span["origin"][1]
                x = span["origin"][0]

                if not text or len(text) < 2:
                    continue
                if sz > 25:  # Watermark
                    continue
                if should_skip_span(text):
                    continue

                # Title zone: y=50-95, font ≥ 13.5pt
                if 50 <= y <= 95 and sz >= 13.5:
                    title_spans.append((y, sz, x, text))

                # Body zone: y=96-355, font ≥ 11pt (slide content, not notes at y≥370)
                elif 96 <= y <= 355 and sz >= 11.0:
                    body_spans.append((y, sz, x, text))

    # Build title
    title_lines = group_spans_to_lines(title_spans)
    if not title_lines:
        return None

    # Clean title lines
    cleaned_titles = []
    for line in title_lines:
        cleaned = re.sub(r'^[\u2022\u2212\u2013\u2014\-•]\s*', '', line).strip()
        if cleaned and len(cleaned) >= 3:
            cleaned_titles.append(cleaned)

    if not cleaned_titles:
        return None

    # Skip pages where keywords won't be useful
    first_title = cleaned_titles[0].lower()
    if first_title in ('course roadmap', 'table of contents', 'course agenda'):
        return (cleaned_titles, [])  # Title only, no keywords

    # Separate body spans into sub-headers (≥13.5pt) and regular text (<13.5pt)
    subheader_spans = [(y, sz, x, t) for y, sz, x, t in body_spans if sz >= 13.5]
    regular_spans = [(y, sz, x, t) for y, sz, x, t in body_spans if sz < 13.5]

    subheader_lines = group_spans_to_lines(subheader_spans, split_columns=True)
    regular_lines = group_spans_to_lines(regular_spans, split_columns=True)

    # Extract keywords from body (pass title for dedup)
    title_text = " ".join(cleaned_titles)
    keywords = extract_keywords_from_text(subheader_lines, regular_lines, title_text)

    return (cleaned_titles, keywords)


def get_printed_page_label(page):
    """Read the printed slide number from a SANS slide PDF page.

    SANS slides have page numbers in two possible locations:
    1. Regular slides: top-right corner, y≈37, x>500, sz≈6.4
    2. Notes/continuation pages: bottom-center, y≈777, x≈303, sz≈10.5
    Returns the page number as int, or None if not found.
    """
    blocks = page.get_text("dict")
    if not blocks or "blocks" not in blocks:
        return None
    for block in blocks["blocks"]:
        if block["type"] != 0:
            continue
        for line_data in block["lines"]:
            for span in line_data["spans"]:
                text = span["text"].strip()
                y = span["origin"][1]
                x = span["origin"][0]
                sz = span["size"]
                if not text.isdigit():
                    continue
                # Location 1: top-right (regular slides)
                if y < 42 and x > 500 and sz < 8:
                    return int(text)
                # Location 2: bottom-center (notes/continuation pages)
                if y > 770 and 250 < x < 350 and 9 < sz < 12:
                    return int(text)
    return None


def process_book(book_label, filename, book_title):
    """Process one book and return list of (page_num, title_lines, keywords) tuples."""
    filepath = BOOKS_DIR / filename
    if not filepath.exists():
        print(f"  WARNING: {filepath} not found, skipping")
        return []

    doc = fitz.open(str(filepath))
    total_pages = len(doc)
    print(f"  {book_label}: {total_pages} pages")

    skip = SKIP_PAGES.get(book_label, [])
    results = []
    last_label = 0
    for pg_idx in range(total_pages):
        if pg_idx in skip:
            continue
        page = doc[pg_idx]
        # Read the actual printed slide number from the PDF
        label = get_printed_page_label(page)
        if label is not None:
            last_label = label
            printed_page = label
        else:
            # Continuation/notes page — use last known slide number
            printed_page = last_label
        data = extract_page_data(page, printed_page)
        if data:
            title_lines, keywords = data
            results.append((printed_page, title_lines, keywords))

    doc.close()
    return results


def main():
    print("=" * 70)
    print("  Extracting Slide Titles + Keywords from SEC549 Books 1-5")
    print("=" * 70)

    all_books = {}

    for book_label, filename, book_title in BOOK_FILES:
        print(f"\nProcessing {book_label}: {book_title}...")
        results = process_book(book_label, filename, book_title)
        all_books[book_label] = (book_title, results)
        print(f"  Extracted {len(results)} pages with titles/keywords")

    # Write the consolidated glossary
    output_file = OUTPUT_DIR / "All_Books_Page_Headers_Glossary.txt"

    with open(output_file, 'w', encoding='utf-8') as f:
        f.write("=" * 95 + "\n")
        f.write("  SEC549 -- SLIDE TITLE & KEYWORD GLOSSARY (All Books)\n")
        f.write("  Slide title + key terms from each page for quick exam lookup\n")
        f.write("=" * 95 + "\n\n")

        for book_label, filename, book_title in BOOK_FILES:
            title, results = all_books[book_label]

            f.write("=" * 95 + "\n")
            f.write(f"  {book_label}: {title}\n")
            f.write("=" * 95 + "\n\n")

            for page_num, title_lines, keywords in results:
                # Title
                main_title = title_lines[0]
                f.write(f"  Page {page_num:>3d} | {main_title}\n")
                for extra in title_lines[1:]:
                    f.write(f"          | {extra}\n")

                # Keywords table
                if keywords:
                    # Format keywords in rows of ~90 chars
                    kw_line = "  Keywords: "
                    lines_out = []
                    current = kw_line
                    for i, kw in enumerate(keywords):
                        sep = ", " if i > 0 else ""
                        addition = sep + kw
                        if len(current) + len(addition) > 90:
                            lines_out.append(current)
                            current = "             " + kw
                        else:
                            current += addition
                    lines_out.append(current)

                    for kw_out in lines_out:
                        f.write(f"          |{kw_out}\n")

                f.write(f"          +{'─' * 84}\n")

            f.write("\n")

    print(f"\n{'=' * 70}")
    print(f"  Output saved to: {output_file}")
    print(f"{'=' * 70}")


if __name__ == "__main__":
    main()
