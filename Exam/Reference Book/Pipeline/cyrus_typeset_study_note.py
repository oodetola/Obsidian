"""
Study Note PDF Typesetter — Custom Design
Clean, readable exam-prep layout with proper visual hierarchy,
card-style page sections, and correct bullet/numbered list handling.

Usage:
    python cyrus_typeset_study_note.py                     # All notes
    python cyrus_typeset_study_note.py "Topics_Cognito"    # Single note
"""

import sys
import re
from pathlib import Path
from reportlab.lib.pagesizes import letter
from reportlab.lib.units import inch
from reportlab.lib.colors import HexColor, Color, black, white
from reportlab.lib.styles import ParagraphStyle
from reportlab.lib.enums import TA_LEFT, TA_CENTER, TA_RIGHT
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle,
    Flowable, KeepTogether, HRFlowable,
)

REF_DIR = Path(r"C:/Users/matth/Downloads/SEC549/Exam/Reference Book")
NOTES_DIR = REF_DIR / "Study Notes"
PDF_DIR = NOTES_DIR / "PDF"

# ── Design Palette ──
NAVY       = HexColor("#1B2A4A")
SLATE      = HexColor("#2D3748")
STEEL      = HexColor("#4A5568")
MEDIUM     = HexColor("#718096")
SOFT       = HexColor("#A0AEC0")
LIGHT_BG   = HexColor("#F7FAFC")
CARD_BG    = HexColor("#FFFFFF")
DIVIDER    = HexColor("#E2E8F0")
ACCENT     = HexColor("#3182CE")   # Blue accent
ACCENT_LT  = HexColor("#EBF4FF")  # Light blue tint
AMBER      = HexColor("#D69E2E")
AMBER_LT   = HexColor("#FEFCBF")
GREEN_DK   = HexColor("#276749")
GREEN_LT   = HexColor("#F0FFF4")
BULLET_COL = HexColor("#3182CE")
REF_COL    = HexColor("#805AD5")   # Purple for references

PAGE_W, PAGE_H = letter
LEFT_M   = 0.65 * inch
RIGHT_M  = 0.55 * inch
TOP_M    = 0.5 * inch
BOTTOM_M = 0.55 * inch
CONTENT_W = PAGE_W - LEFT_M - RIGHT_M


# ─────────────────────────────────────────────────────────
# Custom flowables
# ─────────────────────────────────────────────────────────

class AccentBar(Flowable):
    """Thin colored horizontal bar."""
    def __init__(self, width, height=2, color=ACCENT):
        Flowable.__init__(self)
        self.width = width
        self.height = height
        self.color = color

    def draw(self):
        self.canv.setFillColor(self.color)
        self.canv.roundRect(0, 0, self.width, self.height, 1, fill=1, stroke=0)

    def wrap(self, availWidth, availHeight):
        return (self.width, self.height)


class PageCard(Flowable):
    """A card wrapper with left accent border for a page section."""
    def __init__(self, content_flowables, accent_color=ACCENT, card_width=None):
        Flowable.__init__(self)
        self.content = content_flowables
        self.accent_color = accent_color
        self.card_width = card_width
        self._wrapped_height = 0

    def wrap(self, availWidth, availHeight):
        w = self.card_width or availWidth
        h = 0
        for f in self.content:
            fw, fh = f.wrap(w - 18, availHeight - h)
            h += fh
        self._wrapped_height = h + 12  # padding
        return (w, self._wrapped_height)

    def draw(self):
        w = self.card_width or self.width
        h = self._wrapped_height
        # Card background
        self.canv.setFillColor(CARD_BG)
        self.canv.setStrokeColor(DIVIDER)
        self.canv.setLineWidth(0.5)
        self.canv.roundRect(0, 0, w, h, 3, fill=1, stroke=1)
        # Left accent bar
        self.canv.setFillColor(self.accent_color)
        self.canv.roundRect(0, 0, 3.5, h, 1.5, fill=1, stroke=0)
        # Render content
        y = h - 8
        for f in self.content:
            fw, fh = f.wrap(w - 18, 9999)
            f.drawOn(self.canv, 12, y - fh)
            y -= fh


# ─────────────────────────────────────────────────────────
# Styles
# ─────────────────────────────────────────────────────────

def get_styles():
    s = {}
    s['Title'] = ParagraphStyle(
        'Title', fontSize=22, leading=26, fontName='Helvetica-Bold',
        textColor=NAVY, alignment=TA_LEFT, spaceAfter=2,
    )
    s['Subtitle'] = ParagraphStyle(
        'Subtitle', fontSize=8.5, leading=11, fontName='Helvetica',
        textColor=MEDIUM, alignment=TA_LEFT, spaceAfter=0,
    )
    s['BookHeader'] = ParagraphStyle(
        'BookHeader', fontSize=11, leading=14, fontName='Helvetica-Bold',
        textColor=white, spaceBefore=10, spaceAfter=0,
        leftIndent=8, borderPadding=(5, 8, 5, 8),
    )
    s['PageRef'] = ParagraphStyle(
        'PageRef', fontSize=9.5, leading=12.5, fontName='Helvetica-Bold',
        textColor=ACCENT, spaceBefore=0, spaceAfter=1,
    )
    s['TopicLabel'] = ParagraphStyle(
        'TopicLabel', fontSize=7, leading=9, fontName='Helvetica-Oblique',
        textColor=MEDIUM, spaceBefore=0, spaceAfter=3,
    )
    s['Body'] = ParagraphStyle(
        'Body', fontSize=7.5, leading=10.5, fontName='Helvetica',
        textColor=SLATE, spaceBefore=1.5, spaceAfter=1.5,
    )
    s['BodyBold'] = ParagraphStyle(
        'BodyBold', fontSize=7.5, leading=10.5, fontName='Helvetica-Bold',
        textColor=SLATE, spaceBefore=3, spaceAfter=1.5,
    )
    s['Bullet'] = ParagraphStyle(
        'Bullet', fontSize=7.5, leading=10.5, fontName='Helvetica',
        textColor=SLATE, spaceBefore=1, spaceAfter=1,
        leftIndent=16, bulletIndent=6,
    )
    s['SubBullet'] = ParagraphStyle(
        'SubBullet', fontSize=7, leading=9.5, fontName='Helvetica',
        textColor=STEEL, spaceBefore=0.5, spaceAfter=0.5,
        leftIndent=30, bulletIndent=18,
    )
    s['NumStep'] = ParagraphStyle(
        'NumStep', fontSize=7.5, leading=10.5, fontName='Helvetica',
        textColor=SLATE, spaceBefore=1.5, spaceAfter=1.5,
        leftIndent=16, bulletIndent=4,
    )
    s['RefLink'] = ParagraphStyle(
        'RefLink', fontSize=6.5, leading=8.5, fontName='Courier',
        textColor=REF_COL, spaceBefore=0, spaceAfter=0,
        leftIndent=16,
    )
    s['CheckItem'] = ParagraphStyle(
        'CheckItem', fontSize=8, leading=12, fontName='Helvetica',
        textColor=SLATE, spaceBefore=1, spaceAfter=1,
        leftIndent=16,
    )
    s['FlipBook'] = ParagraphStyle(
        'FlipBook', fontSize=8, leading=10.5, fontName='Helvetica-Bold',
        textColor=NAVY,
    )
    s['FlipPages'] = ParagraphStyle(
        'FlipPages', fontSize=8, leading=10.5, fontName='Courier-Bold',
        textColor=ACCENT,
    )
    s['FlipDomain'] = ParagraphStyle(
        'FlipDomain', fontSize=7.5, leading=10, fontName='Helvetica-Oblique',
        textColor=STEEL,
    )
    s['TH'] = ParagraphStyle(
        'TH', fontSize=7, leading=9.5, fontName='Helvetica-Bold',
        textColor=white,
    )
    s['IndexTerm'] = ParagraphStyle(
        'IndexTerm', fontSize=7, leading=9, fontName='Courier',
        textColor=STEEL, leftIndent=4,
    )
    return s


# ─────────────────────────────────────────────────────────
# Markdown / XML helpers
# ─────────────────────────────────────────────────────────

def esc(text):
    return (text.replace('&', '&amp;').replace('<', '&lt;')
            .replace('>', '&gt;').replace('"', '&quot;'))


def md_to_rl(text):
    text = esc(text)
    text = re.sub(r'\*\*(.+?)\*\*', r'<b>\1</b>', text)
    text = re.sub(r'`(.+?)`', r'<font face="Courier" size="6.5" color="#805AD5">\1</font>', text)
    return text


# ─────────────────────────────────────────────────────────
# Parser
# ─────────────────────────────────────────────────────────

def parse_study_note(md_path):
    text = md_path.read_text(encoding='utf-8')
    lines = text.split('\n')

    note = {
        'title': '', 'subtitle': '',
        'flip_table': [], 'topics': [], 'index_refs': '',
        'books': [], 'checklist': [],
    }

    i = 0
    while i < len(lines):
        line = lines[i].rstrip()

        if line.startswith('# ') and not line.startswith('## '):
            note['title'] = line[2:].strip()
            i += 1; continue

        if line.startswith('Generated:'):
            note['subtitle'] = line.strip()
            i += 1; continue

        if line.startswith('| **(B'):
            m = re.match(r'\|\s*\*\*\(B(\d)\)\*\*\s*\|\s*\*\*(.+?)\*\*\s*\|\s*(.+?)\s*\|', line)
            if m:
                note['flip_table'].append((f"Book {m.group(1)}", m.group(2), m.group(3)))
            i += 1; continue

        if line.startswith('- `') and ' > ' in line:
            m = re.match(r'^- `(.+?)`\s*>\s*(.+)$', line)
            if m:
                note['topics'].append((m.group(1), m.group(2)))
            i += 1; continue

        if line.startswith('**Index entries:**'):
            note['index_refs'] = line.replace('**Index entries:**', '').strip()
            i += 1; continue

        if line.startswith('## Book ') and '--' in line:
            note['books'].append({'header': line[3:].strip(), 'pages': []})
            i += 1; continue

        if line.startswith('### (B') and note['books']:
            note['books'][-1]['pages'].append({'ref': line[4:].strip(), 'paragraphs': []})
            i += 1; continue

        if line.startswith('> ') and note['books'] and note['books'][-1]['pages']:
            para_lines = []
            while i < len(lines) and lines[i].rstrip().startswith('>'):
                content = lines[i].rstrip()
                if content.strip() == '>':
                    if para_lines:
                        note['books'][-1]['pages'][-1]['paragraphs'].append('\n'.join(para_lines))
                        para_lines = []
                else:
                    para_lines.append(content[2:] if content.startswith('> ') else content[1:])
                i += 1
            if para_lines:
                note['books'][-1]['pages'][-1]['paragraphs'].append('\n'.join(para_lines))
            continue

        if re.match(r'^\s*-\s*\[\s*\]', line):
            note['checklist'].append(re.sub(r'^\s*-\s*\[\s*\]\s*', '', line).strip())
            i += 1; continue

        i += 1

    return note


# ─────────────────────────────────────────────────────────
# Builder
# ─────────────────────────────────────────────────────────

def render_paragraph_block(para_text, styles):
    """Render a paragraph block into flowable elements with proper formatting."""
    elements = []
    lines = para_text.split('\n')

    i = 0
    while i < len(lines):
        line = lines[i].strip()
        if not line:
            i += 1; continue

        # Reference URLs
        if line.startswith('http') or re.match(r'^\d+\.\s*https?://', line):
            elements.append(Paragraph(md_to_rl(line), styles['RefLink']))
            i += 1; continue

        # "References:" label
        if line.lower().startswith('references:'):
            elements.append(Spacer(1, 2))
            elements.append(Paragraph(
                f'<font color="{REF_COL.hexval()}">{esc(line)}</font>',
                styles['Body']
            ))
            i += 1; continue

        # Sub-bullets (–, -, indented)
        if re.match(r'^[–\-]\s', line):
            content = re.sub(r'^[–\-]\s*', '', line)
            elements.append(Paragraph(
                f'<font color="{BULLET_COL.hexval()}">&#x2013;</font>  {md_to_rl(content)}',
                styles['SubBullet']
            ))
            i += 1; continue

        # Bullets
        if line.startswith('\u2022') or re.match(r'^•\s', line):
            content = re.sub(r'^[•]\s*', '', line)
            # Collect any sub-bullets that follow
            elements.append(Paragraph(
                f'<font color="{BULLET_COL.hexval()}">&#x2022;</font>  {md_to_rl(content)}',
                styles['Bullet']
            ))
            i += 1; continue

        # Numbered steps: "1.", "2.", etc.
        m = re.match(r'^(\d+)[\.\)]\s*(.*)', line)
        if m:
            num = m.group(1)
            content = m.group(2)
            # If content is empty, join with next non-empty line
            if not content.strip():
                j = i + 1
                while j < len(lines) and not lines[j].strip():
                    j += 1
                if j < len(lines):
                    content = lines[j].strip()
                    i = j
            elements.append(Paragraph(
                f'<font color="{ACCENT.hexval()}"><b>{num}.</b></font>  {md_to_rl(content)}',
                styles['NumStep']
            ))
            i += 1; continue

        # Bold section subheadings — must look like a real heading:
        # Short, title-case, ends with ? or no punctuation, at least 3 words,
        # and does NOT start with common lowercase-continuation words
        skip_words = {'the', 'a', 'an', 'in', 'on', 'to', 'for', 'of', 'and',
                      'or', 'but', 'is', 'are', 'was', 'will', 'can', 'do'}
        if (len(line) < 80 and not line.endswith('.')
                and not line.endswith(',')
                and line[0:1].isupper()
                and line.split()[0].lower() not in skip_words):
            words = line.split()
            caps = sum(1 for w in words if w[0:1].isupper())
            if (len(words) >= 3 and len(words) <= 12
                    and caps >= len(words) * 0.6
                    and '>' not in line):
                elements.append(Paragraph(md_to_rl(line), styles['BodyBold']))
                i += 1; continue

        # Regular body text
        elements.append(Paragraph(md_to_rl(line), styles['Body']))
        i += 1

    return elements


def build_pdf(note, styles):
    elements = []

    # ── TITLE BLOCK ──
    elements.append(Spacer(1, 0.15 * inch))
    elements.append(Paragraph(md_to_rl(note['title']), styles['Title']))
    elements.append(AccentBar(2.5 * inch, 2.5, ACCENT))
    elements.append(Spacer(1, 4))
    elements.append(Paragraph(esc(note['subtitle']), styles['Subtitle']))
    elements.append(Spacer(1, 0.2 * inch))

    # ── FLIP TABLE ──
    if note['flip_table']:
        th = styles['TH']
        table_data = [[
            Paragraph('Book', th),
            Paragraph('Pages', th),
            Paragraph('Domain', th),
        ]]
        for book, pages, domain in note['flip_table']:
            table_data.append([
                Paragraph(esc(book), styles['FlipBook']),
                Paragraph(esc(pages), styles['FlipPages']),
                Paragraph(esc(domain), styles['FlipDomain']),
            ])

        col_widths = [0.65*inch, 2.2*inch, CONTENT_W - 0.65*inch - 2.2*inch]
        t = Table(table_data, colWidths=col_widths, repeatRows=1)
        t.setStyle(TableStyle([
            ('BACKGROUND',   (0, 0), (-1, 0), NAVY),
            ('TEXTCOLOR',    (0, 0), (-1, 0), white),
            ('BACKGROUND',   (0, 1), (-1, -1), ACCENT_LT),
            ('GRID',         (0, 0), (-1, -1), 0.4, DIVIDER),
            ('VALIGN',       (0, 0), (-1, -1), 'MIDDLE'),
            ('LEFTPADDING',  (0, 0), (-1, -1), 6),
            ('RIGHTPADDING', (0, 0), (-1, -1), 6),
            ('TOPPADDING',   (0, 0), (-1, -1), 5),
            ('BOTTOMPADDING',(0, 0), (-1, -1), 5),
            ('ROUNDEDCORNERS', [3, 3, 3, 3]),
        ]))
        elements.append(t)
        elements.append(Spacer(1, 0.12 * inch))

    # ── TOPICS COVERED ──
    if note['topics']:
        topic_rows = []
        for term, refs in note['topics']:
            topic_rows.append(Paragraph(
                f'<font face="Courier" size="6.5" color="{ACCENT.hexval()}">{esc(term)}</font>'
                f'  <font face="Helvetica" size="6.5" color="{MEDIUM.hexval()}">&gt; {esc(refs)}</font>',
                styles['IndexTerm']
            ))
        # Wrap in a light card
        inner = [Paragraph(
            '<font color="#1B2A4A"><b>Topics Covered</b></font>',
            ParagraphStyle('tc', fontSize=8, leading=10, fontName='Helvetica-Bold',
                           textColor=NAVY, spaceAfter=3)
        )] + topic_rows
        if len(topic_rows) > 30:
            # Too many topics for a single card — render without wrapper
            for item in inner:
                elements.append(item)
        else:
            elements.append(PageCard(inner, accent_color=AMBER, card_width=CONTENT_W))
        elements.append(Spacer(1, 0.15 * inch))

    # ── DIVIDER ──
    elements.append(HRFlowable(width='100%', thickness=0.5, color=DIVIDER,
                                spaceBefore=2, spaceAfter=6))

    # ── BOOK SECTIONS ──
    for book in note['books']:
        # Book header bar
        header_table = Table(
            [[Paragraph(esc(book['header']), styles['BookHeader'])]],
            colWidths=[CONTENT_W]
        )
        header_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, -1), NAVY),
            ('LEFTPADDING', (0, 0), (-1, -1), 8),
            ('TOPPADDING', (0, 0), (-1, -1), 6),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 6),
            ('ROUNDEDCORNERS', [4, 4, 0, 0]),
        ]))
        elements.append(header_table)
        elements.append(Spacer(1, 8))

        for page in book['pages']:
            # Parse the ref line for page number and topics
            ref = page['ref']
            page_num = ''
            topics_str = ''
            m = re.match(r'\(B\d\)\s*p\.(\d+)\s*--\s*(.*)', ref)
            if m:
                page_num = m.group(1)
                topics_str = m.group(2)
            else:
                page_num = ref

            # Page card contents
            card_elements = []

            # Page number + topic labels
            card_elements.append(Paragraph(
                f'<font color="{ACCENT.hexval()}" size="10"><b>Page {esc(page_num)}</b></font>',
                styles['PageRef']
            ))
            if topics_str:
                # Split multiple topics by |
                topic_parts = [t.strip() for t in topics_str.split('|')]
                tags_html = '  '.join(
                    f'<font face="Helvetica-Oblique" size="6.5" color="{STEEL.hexval()}">{esc(t)}</font>'
                    for t in topic_parts
                )
                card_elements.append(Paragraph(tags_html, styles['TopicLabel']))

            card_elements.append(Spacer(1, 3))

            # Render all paragraphs
            for para in page['paragraphs']:
                rendered = render_paragraph_block(para, styles)
                card_elements.extend(rendered)
                card_elements.append(Spacer(1, 3))

            # Wrap in a card — skip card wrapper for very large sections to avoid overflow
            total_text = sum(len(p) for p in page['paragraphs'])
            if total_text > 800:
                # Too large for a single non-splittable flowable — render directly
                for ce in card_elements:
                    elements.append(ce)
            else:
                card = PageCard(card_elements, accent_color=ACCENT, card_width=CONTENT_W)
                if len(page['paragraphs']) <= 3:
                    elements.append(KeepTogether([card, Spacer(1, 8)]))
                else:
                    elements.append(card)
            elements.append(Spacer(1, 8))

        elements.append(Spacer(1, 6))

    # ── REVIEW CHECKLIST ──
    if note['checklist']:
        elements.append(Spacer(1, 4))
        check_header = Table(
            [[Paragraph('REVIEW CHECKLIST', styles['BookHeader'])]],
            colWidths=[CONTENT_W]
        )
        check_header.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, -1), GREEN_DK),
            ('LEFTPADDING', (0, 0), (-1, -1), 8),
            ('TOPPADDING', (0, 0), (-1, -1), 5),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 5),
            ('ROUNDEDCORNERS', [4, 4, 0, 0]),
        ]))
        elements.append(check_header)
        elements.append(Spacer(1, 5))

        check_items = []
        for item in note['checklist']:
            check_items.append(Paragraph(
                f'<font size="9" color="{GREEN_DK.hexval()}">&#x2610;</font>'
                f'  {md_to_rl(item)}',
                styles['CheckItem']
            ))

        if len(check_items) > 30:
            for ci in check_items:
                elements.append(ci)
        else:
            card = PageCard(check_items, accent_color=GREEN_DK, card_width=CONTENT_W)
            elements.append(card)

    return elements


# ─────────────────────────────────────────────────────────
# Page template callbacks
# ─────────────────────────────────────────────────────────

_current_title = ""

def _footer(canvas, doc):
    canvas.saveState()
    y = 0.32 * inch
    # Thin line
    canvas.setStrokeColor(DIVIDER)
    canvas.setLineWidth(0.4)
    canvas.line(LEFT_M, y + 8, PAGE_W - RIGHT_M, y + 8)
    # Left: title
    canvas.setFont('Helvetica', 6.5)
    canvas.setFillColor(MEDIUM)
    canvas.drawString(LEFT_M, y, f"SEC549  |  {_current_title}")
    # Right: page number
    canvas.drawRightString(PAGE_W - RIGHT_M, y, f"Page {doc.page}")
    canvas.restoreState()


# ─────────────────────────────────────────────────────────
# Main
# ─────────────────────────────────────────────────────────

def typeset_note(md_path):
    global _current_title
    PDF_DIR.mkdir(parents=True, exist_ok=True)
    pdf_name = md_path.stem + ".pdf"
    pdf_path = PDF_DIR / pdf_name

    print(f"  Typesetting: {md_path.name}")
    note = parse_study_note(md_path)
    _current_title = note['title']
    styles = get_styles()
    elements = build_pdf(note, styles)

    doc = SimpleDocTemplate(
        str(pdf_path), pagesize=letter,
        leftMargin=LEFT_M, rightMargin=RIGHT_M,
        topMargin=TOP_M, bottomMargin=BOTTOM_M,
    )
    doc.build(elements, onFirstPage=_footer, onLaterPages=_footer)

    size_kb = pdf_path.stat().st_size / 1024
    print(f"    -> {pdf_name} ({size_kb:.0f} KB)")
    return pdf_path


def main():
    print(f"\n{'='*60}")
    print(f"  STUDY NOTE PDF TYPESETTER")
    print(f"{'='*60}\n")

    if len(sys.argv) > 1:
        keyword = sys.argv[1].strip()
        md_file = NOTES_DIR / f"StudyNote_{keyword}.md"
        if not md_file.exists():
            print(f"  ERROR: {md_file} not found.")
            sys.exit(1)
        typeset_note(md_file)
    else:
        md_files = sorted(NOTES_DIR.glob("StudyNote_*.md"))
        if not md_files:
            print("  No study notes found.")
            sys.exit(0)
        print(f"  Found {len(md_files)} study note(s)\n")
        for md_file in md_files:
            typeset_note(md_file)

    print(f"\n{'='*60}")
    print(f"  DONE -- PDFs in: {PDF_DIR}")
    print(f"{'='*60}")


if __name__ == '__main__':
    main()
