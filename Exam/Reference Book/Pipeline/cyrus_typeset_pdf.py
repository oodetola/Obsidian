"""
Cyrus -- Phase D: Typeset & Produce Print-Ready PDF
Generates a professional, print-optimized PDF reference book from the
assembled markdown content.

Uses reportlab for PDF generation with:
- Two-column layout for index sections
- Color-coded section headers
- Running page headers
- Optimized for US Letter paper with spiral binding margins
"""

from reportlab.lib.pagesizes import letter
from reportlab.lib.units import inch
from reportlab.lib.colors import HexColor, black, white
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.enums import TA_LEFT, TA_CENTER, TA_JUSTIFY
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle,
    PageBreak, KeepTogether, Frame, PageTemplate, BaseDocTemplate,
    NextPageTemplate
)
from reportlab.platypus.flowables import BalancedColumns
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from pathlib import Path
import re

EXAM_DIR = Path(r"C:/Users/matth/Downloads/SEC549/Exam")
REF_DIR = EXAM_DIR / "Reference Book"
OUTPUT_PDF = REF_DIR / "SEC549_Exam_Reference_Book.pdf"

# Colors
AWS_ORANGE = HexColor("#FF9900")
AZURE_BLUE = HexColor("#0078D4")
GCP_GREEN = HexColor("#34A853")
SECTION_BG = HexColor("#2C3E50")
HEADER_TEXT = HexColor("#FFFFFF")
LIGHT_GRAY = HexColor("#F5F5F5")
MED_GRAY = HexColor("#E0E0E0")
DARK_GRAY = HexColor("#333333")


def get_styles():
    """Build all paragraph styles for the reference book."""
    styles = getSampleStyleSheet()

    styles.add(ParagraphStyle(
        name='BookTitle',
        fontSize=18,
        leading=22,
        alignment=TA_CENTER,
        spaceAfter=6,
        textColor=DARK_GRAY,
        fontName='Helvetica-Bold',
    ))

    styles.add(ParagraphStyle(
        name='BookSubtitle',
        fontSize=11,
        leading=14,
        alignment=TA_CENTER,
        spaceAfter=4,
        textColor=DARK_GRAY,
        fontName='Helvetica',
    ))

    styles.add(ParagraphStyle(
        name='SectionHeader',
        fontSize=14,
        leading=18,
        spaceBefore=12,
        spaceAfter=6,
        textColor=white,
        fontName='Helvetica-Bold',
        backColor=SECTION_BG,
        leftIndent=6,
        rightIndent=6,
        borderPadding=(4, 6, 4, 6),
    ))

    styles.add(ParagraphStyle(
        name='SubHeader',
        fontSize=10,
        leading=13,
        spaceBefore=8,
        spaceAfter=4,
        textColor=DARK_GRAY,
        fontName='Helvetica-Bold',
        borderWidth=0,
        borderColor=MED_GRAY,
        borderPadding=(2, 0, 2, 0),
    ))

    styles.add(ParagraphStyle(
        name='BodyText8',
        fontSize=8,
        leading=10,
        spaceBefore=1,
        spaceAfter=1,
        textColor=black,
        fontName='Helvetica',
    ))

    styles.add(ParagraphStyle(
        name='CodeText',
        fontSize=7,
        leading=9,
        spaceBefore=1,
        spaceAfter=1,
        textColor=DARK_GRAY,
        fontName='Courier',
        leftIndent=10,
    ))

    styles.add(ParagraphStyle(
        name='IndexEntry',
        fontSize=7,
        leading=8.5,
        spaceBefore=0,
        spaceAfter=0,
        textColor=black,
        fontName='Helvetica',
    ))

    styles.add(ParagraphStyle(
        name='IndexLetter',
        fontSize=10,
        leading=12,
        spaceBefore=6,
        spaceAfter=2,
        textColor=SECTION_BG,
        fontName='Helvetica-Bold',
    ))

    styles.add(ParagraphStyle(
        name='HowToUse',
        fontSize=8,
        leading=10,
        spaceBefore=2,
        spaceAfter=2,
        textColor=DARK_GRAY,
        fontName='Helvetica',
    ))

    styles.add(ParagraphStyle(
        name='TableHeader',
        fontSize=7,
        leading=9,
        textColor=white,
        fontName='Helvetica-Bold',
        alignment=TA_LEFT,
    ))

    styles.add(ParagraphStyle(
        name='TableCell',
        fontSize=7,
        leading=9,
        textColor=black,
        fontName='Helvetica',
        alignment=TA_LEFT,
    ))

    return styles


def escape_xml(text):
    """Escape XML special characters for reportlab paragraphs."""
    return (text
            .replace('&', '&amp;')
            .replace('<', '&lt;')
            .replace('>', '&gt;')
            .replace('"', '&quot;'))


def make_table(headers, rows, col_widths=None):
    """Create a formatted table."""
    # Build table data
    header_style = ParagraphStyle('th', fontSize=7, leading=9, fontName='Helvetica-Bold', textColor=white)
    cell_style = ParagraphStyle('td', fontSize=7, leading=9, fontName='Helvetica')

    table_data = [[Paragraph(escape_xml(h), header_style) for h in headers]]
    for row in rows:
        table_data.append([Paragraph(escape_xml(str(c)), cell_style) for c in row])

    if col_widths is None:
        col_widths = [6.5 * inch / len(headers)] * len(headers)

    t = Table(table_data, colWidths=col_widths, repeatRows=1)

    style_cmds = [
        ('BACKGROUND', (0, 0), (-1, 0), SECTION_BG),
        ('TEXTCOLOR', (0, 0), (-1, 0), white),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, 0), 7),
        ('FONTSIZE', (0, 1), (-1, -1), 7),
        ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
        ('VALIGN', (0, 0), (-1, -1), 'TOP'),
        ('GRID', (0, 0), (-1, -1), 0.5, MED_GRAY),
        ('LEFTPADDING', (0, 0), (-1, -1), 3),
        ('RIGHTPADDING', (0, 0), (-1, -1), 3),
        ('TOPPADDING', (0, 0), (-1, -1), 2),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 2),
    ]
    # Alternating row colors
    for i in range(1, len(table_data)):
        if i % 2 == 0:
            style_cmds.append(('BACKGROUND', (0, i), (-1, i), LIGHT_GRAY))

    t.setStyle(TableStyle(style_cmds))
    return t


def build_cover_page(styles):
    """Build the cover/front matter page."""
    elements = []
    elements.append(Spacer(1, 1.5 * inch))
    elements.append(Paragraph("SEC549 GIAC EXAM", styles['BookTitle']))
    elements.append(Paragraph("REFERENCE BOOK", styles['BookTitle']))
    elements.append(Spacer(1, 0.3 * inch))
    elements.append(Paragraph("Cloud Security Architecture and Operations", styles['BookSubtitle']))
    elements.append(Paragraph("Prepared by Cyrus -- GIAC Exam Reference Architect", styles['BookSubtitle']))
    elements.append(Spacer(1, 0.5 * inch))

    # How to use
    elements.append(Paragraph("HOW TO USE THIS REFERENCE", styles['SubHeader']))
    how_to = [
        "This book is a <b>LOOKUP TOOL</b>, not a study guide. Find answers in under 20 seconds.",
        "",
        "<b>NAVIGATION:</b>",
        "1. TOPIC SECTIONS -- for concept questions (IAM, Network, Encryption, etc.)",
        "2. COMPARISON MATRICES -- for cross-cloud questions (AWS vs Azure vs GCP)",
        "3. CLI CHEAT SHEET -- for command syntax questions",
        "4. ACRONYM GLOSSARY -- for terminology questions",
        "5. MASTER INDEX -- look up any term, find Book/Page in your SANS materials",
        "",
        "<b>EXAM FORMAT:</b> 100-115 MCQ | 2-3 hours | ~1-1.5 min/question | Open book",
        "",
        "<b>PAGE REFS:</b> (B1) 42 = Book 1, page 42 | (B3) 95 = Book 3, page 95",
    ]
    for line in how_to:
        elements.append(Paragraph(escape_xml(line) if not line.startswith('<') else line, styles['HowToUse']))

    elements.append(Spacer(1, 0.3 * inch))

    # Book mapping table
    elements.append(Paragraph("EXAM DOMAIN TO BOOK MAPPING", styles['SubHeader']))
    book_map = make_table(
        ["Book", "Pages", "Primary Topics"],
        [
            ["Book 1", "144", "IAM Foundations, RBAC/ABAC/PBAC, AWS IdC, Azure Entra ID, GCP IAM, SCPs, Federation"],
            ["Book 2", "137", "Auth Deep Dive: SAML/OIDC/OAuth, Cognito, STS, Managed Identity, Workload Identity, Zero Trust"],
            ["Book 3", "151", "Network Security: VPC/VNet, SGs/NSGs, Segmentation, Private Link, Transit GW, DNS, DDoS"],
            ["Book 4", "158", "Governance & Data: Encryption, KMS, Secrets, Compliance, CSPM, Container Security, Audit"],
            ["Book 5", "103", "Detection & Response: SIEM, CloudTrail/Monitor/Audit Logs, GuardDuty/Defender/SCC, IR"],
        ],
        col_widths=[0.6*inch, 0.5*inch, 5.4*inch]
    )
    elements.append(book_map)
    elements.append(PageBreak())
    return elements


def build_iam_section(styles):
    """Build Section 1: IAM."""
    elements = []
    elements.append(Paragraph("SECTION 1: IDENTITY &amp; ACCESS MANAGEMENT", styles['SectionHeader']))

    # IAM comparison table
    elements.append(Paragraph("1.1 IAM Service Comparison", styles['SubHeader']))
    elements.append(make_table(
        ["Feature", "AWS", "Azure", "GCP"],
        [
            ["IAM Service", "AWS IAM", "Entra ID (Azure AD)", "Cloud IAM"],
            ["Identity Center", "IAM Identity Center", "Entra ID", "Cloud Identity"],
            ["SSO", "IAM IdC SSO", "Entra ID SSO", "Cloud Identity SSO"],
            ["Root/Global Admin", "Root Account", "Global Administrator", "Super Admin"],
            ["Service Account", "IAM Role (for svc)", "Managed Identity", "Service Account"],
            ["Temporary Creds", "STS AssumeRole", "Managed Identity Token", "SA Key (avoid) / WI"],
            ["MFA", "IAM MFA / IdC MFA", "Entra MFA", "2-Step Verification"],
            ["Conditional Access", "IAM Conditions", "Conditional Access", "Access Context Mgr"],
            ["Privileged Access", "N/A (use SCPs)", "PIM", "PAM (preview)"],
            ["External Identity", "Cognito / SAML/OIDC", "B2B / B2C", "Workload Identity Fed"],
            ["Access Review", "Access Analyzer", "Access Reviews", "IAM Recommender"],
        ],
        col_widths=[1.2*inch, 1.5*inch, 1.8*inch, 2.0*inch]
    ))

    # Access control models
    elements.append(Paragraph("1.2 Access Control Models", styles['SubHeader']))
    elements.append(make_table(
        ["Model", "Description", "Where Used"],
        [
            ["RBAC", "Role-Based Access Control", "Azure (primary), AWS (IAM roles), GCP"],
            ["ABAC", "Attribute-Based Access Control", "AWS (tags), Azure (conditions), GCP"],
            ["PBAC", "Policy-Based Access Control", "AWS IAM policies, GCP IAM bindings"],
            ["ACL", "Access Control Lists", "AWS S3, Network ACLs"],
            ["ReBAC", "Relationship-Based Access", "Google Zanzibar (internal)"],
        ],
        col_widths=[0.7*inch, 2.3*inch, 3.5*inch]
    ))

    # Hierarchy notes
    elements.append(Paragraph("1.3 Key IAM Distinctions", styles['SubHeader']))
    distinctions = [
        "<b>AWS:</b> SCP = DENY guardrail (restricts, not grants). Effective permissions = Identity Policy INTERSECT Permission Boundary INTERSECT SCP",
        "<b>Azure:</b> RBAC inherited down hierarchy. Deny assignments override allow. Conditional Access = context-aware gating.",
        "<b>GCP:</b> IAM is additive (allow-only). Deny policies now exist but separate. Org Policy = constraints like SCPs.",
    ]
    for d in distinctions:
        elements.append(Paragraph(d, styles['BodyText8']))
        elements.append(Spacer(1, 3))

    elements.append(PageBreak())
    return elements


def build_auth_section(styles):
    """Build Section 2: Authentication & Federation."""
    elements = []
    elements.append(Paragraph("SECTION 2: AUTHENTICATION &amp; FEDERATION", styles['SectionHeader']))

    elements.append(Paragraph("2.1 Federation Protocols", styles['SubHeader']))
    elements.append(make_table(
        ["Protocol", "Purpose", "Token Type", "Key Flow"],
        [
            ["SAML 2.0", "Enterprise SSO", "XML Assertion", "Browser redirect, POST binding"],
            ["OIDC", "Modern auth (OpenID)", "JWT ID Token", "Authorization Code + PKCE"],
            ["OAuth 2.0", "Authorization", "Access Token", "Auth Code, Client Credentials"],
            ["Kerberos", "On-prem AD auth", "TGT/TGS", "KDC ticket exchange"],
            ["LDAP", "Directory queries", "N/A", "Bind + search"],
        ],
        col_widths=[0.8*inch, 1.5*inch, 1.2*inch, 3.0*inch]
    ))

    elements.append(Paragraph("<b>KEY:</b> SAML = authentication | OAuth = authorization | OIDC = authentication ON TOP of OAuth", styles['BodyText8']))
    elements.append(Spacer(1, 4))

    elements.append(Paragraph("2.2 Federation Across Clouds", styles['SubHeader']))
    elements.append(make_table(
        ["Scenario", "AWS", "Azure", "GCP"],
        [
            ["On-prem AD", "SAML to IAM/IdC", "Entra Connect Sync", "Cloud Identity + SAML"],
            ["Cross-cloud", "OIDC/STS AssumeRole", "Workload Identity Fed", "Workload Identity Fed"],
            ["CI/CD workload", "OIDC Provider + AssumeRole", "Federated Credentials", "Workload Identity Prov."],
            ["External users", "Cognito User Pools", "Azure AD B2C", "Identity Platform"],
            ["M2M", "IAM Role + STS", "Managed Identity", "Service Account"],
        ],
        col_widths=[1.2*inch, 1.8*inch, 1.7*inch, 1.8*inch]
    ))

    elements.append(Paragraph("2.3 AWS STS API Calls", styles['SubHeader']))
    elements.append(make_table(
        ["API Call", "Use Case"],
        [
            ["AssumeRole", "Cross-account access, temporary elevated privileges"],
            ["AssumeRoleWithSAML", "SAML-based federation from IdP"],
            ["AssumeRoleWithWebIdentity", "OIDC federation (Cognito, GitHub, etc.)"],
            ["GetFederationToken", "Temporary creds for federated users"],
            ["GetSessionToken", "MFA-authenticated temporary creds"],
            ["GetCallerIdentity", "Who am I? -- verify current identity"],
        ],
        col_widths=[2.5*inch, 4.0*inch]
    ))

    elements.append(Paragraph("2.4 Azure Managed Identity", styles['SubHeader']))
    mi_notes = [
        "<b>System-Assigned:</b> Tied to resource lifecycle. Use for single-resource auth.",
        "<b>User-Assigned:</b> Independent lifecycle. Share across resources.",
        "<b>KEY:</b> No secrets to rotate. Token via IMDS (169.254.169.254).",
    ]
    for n in mi_notes:
        elements.append(Paragraph(n, styles['BodyText8']))

    elements.append(Paragraph("2.5 GCP Service Accounts", styles['SubHeader']))
    sa_notes = [
        "<b>Default:</b> Auto-created, overly permissive -- AVOID in production.",
        "<b>User-Managed:</b> Created by admin, custom permissions.",
        "<b>KEY:</b> SA keys are long-lived creds -- prefer Workload Identity (keyless).",
    ]
    for n in sa_notes:
        elements.append(Paragraph(n, styles['BodyText8']))

    elements.append(PageBreak())
    return elements


def build_network_section(styles):
    """Build Section 3: Network Security."""
    elements = []
    elements.append(Paragraph("SECTION 3: NETWORK SECURITY &amp; SEGMENTATION", styles['SectionHeader']))

    elements.append(Paragraph("3.1 Network Security Controls", styles['SubHeader']))
    elements.append(make_table(
        ["Control", "AWS", "Azure", "GCP"],
        [
            ["Virtual Network", "VPC", "VNet", "VPC"],
            ["Stateful Firewall", "Security Group", "NSG", "Firewall Rules"],
            ["Stateless Firewall", "NACL", "N/A", "N/A"],
            ["Web App Firewall", "AWS WAF", "Azure WAF", "Cloud Armor"],
            ["DDoS Protection", "Shield (Std/Adv)", "DDoS Protection", "Cloud Armor"],
            ["Network Firewall", "Network Firewall", "Azure Firewall", "Cloud NGFW"],
            ["Flow Logs", "VPC Flow Logs", "NSG Flow Logs", "VPC Flow Logs"],
        ],
        col_widths=[1.3*inch, 1.6*inch, 1.8*inch, 1.8*inch]
    ))

    elements.append(Paragraph("3.2 Private Connectivity", styles['SubHeader']))
    elements.append(make_table(
        ["Feature", "AWS", "Azure", "GCP"],
        [
            ["Private Endpoint", "PrivateLink", "Private Endpoint", "Private Service Connect"],
            ["Service Endpoint", "Gateway EP (S3,DDB)", "Service Endpoint", "Private Google Access"],
            ["Private DNS", "Route 53 Private", "Private DNS Zone", "Cloud DNS Private"],
            ["Hybrid Connect", "Direct Connect", "ExpressRoute", "Cloud Interconnect"],
            ["VPN", "Site-to-Site VPN", "VPN Gateway", "Cloud VPN"],
            ["Peering", "VPC Peering", "VNet Peering", "VPC Peering"],
            ["Transit", "Transit Gateway", "Virtual WAN", "N/A (use peering)"],
        ],
        col_widths=[1.3*inch, 1.6*inch, 1.8*inch, 1.8*inch]
    ))

    elements.append(Paragraph("3.3 Security Group / NSG Key Facts", styles['SubHeader']))
    sg_notes = [
        "<b>AWS SG:</b> STATEFUL, deny-all-inbound default, ALLOW-only rules, applied at ENI level",
        "<b>AWS NACL:</b> STATELESS, allow-all default, ALLOW+DENY, processed in order, subnet level",
        "<b>Azure NSG:</b> STATEFUL, priority-based (lower=higher), subnet or NIC level",
        "<b>GCP Firewall:</b> STATEFUL, deny-all-ingress default, priority-based, network tags or SA",
    ]
    for n in sg_notes:
        elements.append(Paragraph(n, styles['BodyText8']))
        elements.append(Spacer(1, 2))

    elements.append(PageBreak())
    return elements


def build_data_section(styles):
    """Build Section 4: Data Protection."""
    elements = []
    elements.append(Paragraph("SECTION 4: DATA PROTECTION &amp; ENCRYPTION", styles['SectionHeader']))

    elements.append(Paragraph("4.1 Encryption Comparison", styles['SubHeader']))
    elements.append(make_table(
        ["Feature", "AWS", "Azure", "GCP"],
        [
            ["KMS", "AWS KMS", "Azure Key Vault", "Cloud KMS"],
            ["HSM", "CloudHSM", "Managed HSM", "Cloud HSM"],
            ["Default Encrypt", "SSE-S3 / SSE-KMS", "Storage SSE", "Google-managed key"],
            ["Customer Key", "CMK in KMS", "CMK in Key Vault", "CMEK in Cloud KMS"],
            ["Customer-Supplied", "SSE-C", "N/A", "CSEK"],
            ["Key Rotation", "Auto 1yr / manual", "Auto / manual", "Auto 1yr / manual"],
            ["Secrets", "Secrets Manager", "Key Vault Secrets", "Secret Manager"],
            ["Certs", "ACM", "Key Vault Certs", "Certificate Authority"],
        ],
        col_widths=[1.3*inch, 1.6*inch, 1.8*inch, 1.8*inch]
    ))

    elements.append(Paragraph("4.2 Key Concepts", styles['SubHeader']))
    enc_notes = [
        "<b>Envelope Encryption:</b> Encrypt data with DEK, encrypt DEK with KEK (master key)",
        "<b>At Rest:</b> Data on disk -- use KMS/Key Vault/Cloud KMS",
        "<b>In Transit:</b> Data over network -- TLS 1.2+, mTLS for service mesh, VPN for hybrid",
        "<b>Key Hierarchy:</b> Root Key &gt; Key Encryption Key (KEK) &gt; Data Encryption Key (DEK)",
    ]
    for n in enc_notes:
        elements.append(Paragraph(n, styles['BodyText8']))
        elements.append(Spacer(1, 2))

    elements.append(PageBreak())
    return elements


def build_logging_section(styles):
    """Build Section 5: Logging & Detection."""
    elements = []
    elements.append(Paragraph("SECTION 5: LOGGING, MONITORING &amp; DETECTION", styles['SectionHeader']))

    elements.append(Paragraph("5.1 Logging Services", styles['SubHeader']))
    elements.append(make_table(
        ["Feature", "AWS", "Azure", "GCP"],
        [
            ["API/Control Plane", "CloudTrail", "Activity Log", "Cloud Audit Logs"],
            ["Data Plane", "CT Data Events", "Diagnostic Settings", "Data Access Logs"],
            ["Network", "VPC Flow Logs", "NSG Flow Logs", "VPC Flow Logs"],
            ["Compute Logs", "CloudWatch Logs", "Log Analytics", "Cloud Logging"],
            ["SIEM", "SecurityHub", "Sentinel", "Security Command Center"],
            ["Threat Detection", "GuardDuty", "Defender for Cloud", "SCC"],
            ["Config Compliance", "AWS Config", "Azure Policy", "Security Health Analytics"],
        ],
        col_widths=[1.3*inch, 1.6*inch, 1.8*inch, 1.8*inch]
    ))

    elements.append(Paragraph("5.2 Critical Logs to Enable", styles['SubHeader']))
    log_notes = [
        "<b>AWS:</b> CloudTrail ALL regions + data events, S3 logging, VPC Flow Logs, GuardDuty all regions, Config rules",
        "<b>Azure:</b> Activity Log to Log Analytics, Diagnostics on all resources, NSG Flow Logs v2, Defender + Sentinel",
        "<b>GCP:</b> Admin Activity (always on), Data Access (enable!), VPC Flow Logs, export to BigQuery, SCC Premium",
    ]
    for n in log_notes:
        elements.append(Paragraph(n, styles['BodyText8']))
        elements.append(Spacer(1, 2))

    elements.append(Paragraph("5.3 Incident Response Phases", styles['SubHeader']))
    elements.append(make_table(
        ["Phase", "Key Actions"],
        [
            ["Preparation", "Enable logging, set up alerts, define playbooks"],
            ["Detection", "GuardDuty/Defender/SCC findings, SIEM alerts"],
            ["Containment", "Isolate (SG/NSG), revoke creds, snapshot evidence"],
            ["Eradication", "Remove malware, patch vulns, rotate keys"],
            ["Recovery", "Restore from clean backup, validate, re-enable"],
            ["Lessons Learned", "Update playbooks, improve detection, share findings"],
        ],
        col_widths=[1.3*inch, 5.2*inch]
    ))

    elements.append(PageBreak())
    return elements


def build_zerotrust_section(styles):
    """Build Section 6: Zero Trust & Governance."""
    elements = []
    elements.append(Paragraph("SECTION 6: ZERO TRUST &amp; GOVERNANCE", styles['SectionHeader']))

    elements.append(Paragraph("6.1 Zero Trust Principles", styles['SubHeader']))
    zt_notes = [
        "1. Never trust, always verify",
        "2. Assume breach",
        "3. Verify explicitly (identity, device, location, behavior)",
        "4. Least privilege access",
        "5. Microsegmentation",
        "6. Continuous validation",
        "",
        "<b>CISA ZT Maturity Model Pillars:</b> Identity | Devices | Networks | Apps/Workloads | Data",
    ]
    for n in zt_notes:
        elements.append(Paragraph(n, styles['BodyText8']))

    elements.append(Paragraph("6.2 Shared Responsibility Model", styles['SubHeader']))
    elements.append(make_table(
        ["Layer", "IaaS", "PaaS", "SaaS"],
        [
            ["Data", "Customer", "Customer", "Customer"],
            ["Applications", "Customer", "Customer", "Provider"],
            ["Runtime/OS", "Customer", "Provider", "Provider"],
            ["Virtualization", "Provider", "Provider", "Provider"],
            ["Network/Physical", "Provider", "Provider", "Provider"],
        ],
        col_widths=[1.5*inch, 1.7*inch, 1.6*inch, 1.7*inch]
    ))
    elements.append(Paragraph("<b>KEY:</b> Customer ALWAYS responsible for data classification and access control.", styles['BodyText8']))

    elements.append(Paragraph("6.3 Governance Comparison", styles['SubHeader']))
    elements.append(make_table(
        ["Feature", "AWS", "Azure", "GCP"],
        [
            ["Policy Guardrails", "SCPs (Org)", "Azure Policy", "Organization Policy"],
            ["Compliance", "AWS Config Rules", "Policy (built-in)", "Security Health Analytics"],
            ["Landing Zone", "Control Tower", "Azure Landing Zones", "Cloud Foundation Toolkit"],
            ["Tagging", "Tag Policies", "Policy (tags)", "Labels"],
            ["Blueprints", "Service Catalog", "Blueprints", "Deployment Manager"],
        ],
        col_widths=[1.3*inch, 1.6*inch, 1.8*inch, 1.8*inch]
    ))

    elements.append(PageBreak())
    return elements


def build_container_section(styles):
    """Build Section 7: Container Security."""
    elements = []
    elements.append(Paragraph("SECTION 7: CONTAINER &amp; KUBERNETES SECURITY", styles['SectionHeader']))

    elements.append(Paragraph("7.1 Managed Kubernetes Comparison", styles['SubHeader']))
    elements.append(make_table(
        ["Feature", "AWS EKS", "Azure AKS", "GCP GKE"],
        [
            ["Node Auth", "IAM Roles for SA", "Managed Identity", "Workload Identity"],
            ["Network Policy", "Calico", "Azure NPM / Calico", "Calico / Dataplane V2"],
            ["Image Scanning", "ECR Scanning", "Defender for Containers", "Artifact Analysis"],
            ["Registry", "ECR", "ACR", "Artifact Registry"],
            ["Secrets", "Secrets Manager CSI", "Key Vault CSI", "Secret Manager CSI"],
            ["Binary Auth", "N/A (Kyverno)", "N/A (Gatekeeper)", "Binary Authorization"],
        ],
        col_widths=[1.3*inch, 1.6*inch, 1.8*inch, 1.8*inch]
    ))

    elements.append(Paragraph("7.2 Container Security Checklist", styles['SubHeader']))
    checklist = [
        "[ ] Minimal base images (distroless, Alpine)",
        "[ ] Scan images in CI/CD",
        "[ ] Sign/verify images (cosign)",
        "[ ] Run as non-root",
        "[ ] Read-only root filesystem",
        "[ ] Pod Security Standards (Restricted)",
        "[ ] Network Policies for pod-to-pod",
        "[ ] Workload Identity (not node creds)",
        "[ ] Encrypt secrets in etcd",
        "[ ] K8s API audit logging",
    ]
    for c in checklist:
        elements.append(Paragraph(escape_xml(c), styles['BodyText8']))

    elements.append(PageBreak())
    return elements


def build_cli_section(styles):
    """Build CLI Cheat Sheet section."""
    elements = []
    elements.append(Paragraph("CLI CHEAT SHEET -- COMMON SECURITY COMMANDS", styles['SectionHeader']))

    # AWS
    elements.append(Paragraph("AWS CLI", styles['SubHeader']))
    aws_cmds = [
        ("aws sts get-caller-identity", "Who am I?"),
        ("aws sts assume-role --role-arn &lt;ARN&gt; --role-session-name &lt;n&gt;", "Assume role"),
        ("aws iam list-users", "List IAM users"),
        ("aws iam list-roles", "List IAM roles"),
        ("aws iam list-attached-user-policies --user-name &lt;u&gt;", "User policies"),
        ("aws iam list-access-keys --user-name &lt;u&gt;", "Check for keys"),
        ("aws organizations list-accounts", "Org accounts"),
        ("aws cloudtrail describe-trails", "List trails"),
        ("aws guardduty list-detectors", "GuardDuty status"),
        ("aws ec2 describe-vpcs", "List VPCs"),
        ("aws ec2 describe-security-groups", "List SGs"),
        ("aws kms list-keys", "KMS keys"),
        ("aws s3api get-bucket-encryption --bucket &lt;n&gt;", "S3 encryption"),
    ]
    elements.append(make_table(
        ["Command", "Purpose"],
        [[c, p] for c, p in aws_cmds],
        col_widths=[4.5*inch, 2.0*inch]
    ))

    # Azure
    elements.append(Paragraph("Azure CLI", styles['SubHeader']))
    az_cmds = [
        ("az account show", "Current context"),
        ("az ad user list", "List AD users"),
        ("az ad sp list --all", "Service principals"),
        ("az role assignment list --all", "RBAC assignments"),
        ("az role definition list --custom-role-only true", "Custom roles"),
        ("az identity list", "Managed identities"),
        ("az network vnet list", "List VNets"),
        ("az network nsg list", "List NSGs"),
        ("az keyvault list", "Key Vaults"),
    ]
    elements.append(make_table(
        ["Command", "Purpose"],
        [[c, p] for c, p in az_cmds],
        col_widths=[4.5*inch, 2.0*inch]
    ))

    # GCP
    elements.append(Paragraph("gcloud CLI", styles['SubHeader']))
    gcp_cmds = [
        ("gcloud auth list", "Active accounts"),
        ("gcloud projects get-iam-policy &lt;PROJECT&gt;", "IAM bindings"),
        ("gcloud iam service-accounts list", "Service accounts"),
        ("gcloud organizations list", "Organizations"),
        ("gcloud logging logs list", "Available logs"),
        ("gcloud compute networks list", "VPCs"),
        ("gcloud compute firewall-rules list", "Firewall rules"),
        ("gcloud kms keys list --location &lt;L&gt; --keyring &lt;K&gt;", "KMS keys"),
    ]
    elements.append(make_table(
        ["Command", "Purpose"],
        [[c, p] for c, p in gcp_cmds],
        col_widths=[4.5*inch, 2.0*inch]
    ))

    # kubectl
    elements.append(Paragraph("kubectl", styles['SubHeader']))
    k_cmds = [
        ("kubectl auth can-i --list", "My permissions"),
        ("kubectl get pods --all-namespaces", "All pods"),
        ("kubectl get networkpolicies -A", "Network policies"),
        ("kubectl get clusterroles", "RBAC cluster roles"),
    ]
    elements.append(make_table(
        ["Command", "Purpose"],
        [[c, p] for c, p in k_cmds],
        col_widths=[4.5*inch, 2.0*inch]
    ))

    elements.append(PageBreak())
    return elements


def build_acronym_section(styles):
    """Build acronym glossary."""
    elements = []
    elements.append(Paragraph("ACRONYM GLOSSARY", styles['SectionHeader']))

    acronyms = [
        ("ABAC", "Attribute-Based Access Control"),
        ("ACL", "Access Control List"),
        ("ACM", "AWS Certificate Manager"),
        ("AKS", "Azure Kubernetes Service"),
        ("ARN", "Amazon Resource Name"),
        ("CASB", "Cloud Access Security Broker"),
        ("CIEM", "Cloud Infrastructure Entitlement Management"),
        ("CIDR", "Classless Inter-Domain Routing"),
        ("CMEK", "Customer-Managed Encryption Key"),
        ("CMK", "Customer Master Key (AWS KMS)"),
        ("CNAPP", "Cloud-Native Application Protection Platform"),
        ("CSEK", "Customer-Supplied Encryption Key"),
        ("CSPM", "Cloud Security Posture Management"),
        ("CWPP", "Cloud Workload Protection Platform"),
        ("DEK", "Data Encryption Key"),
        ("DDoS", "Distributed Denial of Service"),
        ("DLP", "Data Loss Prevention"),
        ("DNS", "Domain Name System"),
        ("EBS", "Elastic Block Store"),
        ("EC2", "Elastic Compute Cloud"),
        ("ECR", "Elastic Container Registry"),
        ("EKS", "Elastic Kubernetes Service"),
        ("ENI", "Elastic Network Interface"),
        ("FIDO2", "Fast Identity Online v2"),
        ("GCS", "Google Cloud Storage"),
        ("GKE", "Google Kubernetes Engine"),
        ("HSM", "Hardware Security Module"),
        ("IaC", "Infrastructure as Code"),
        ("IAM", "Identity and Access Management"),
        ("IdC", "Identity Center (AWS)"),
        ("IDP", "Identity Provider"),
        ("IMDS", "Instance Metadata Service (169.254.169.254)"),
        ("JIT", "Just-In-Time (access)"),
        ("JWT", "JSON Web Token"),
        ("KEK", "Key Encryption Key"),
        ("KMS", "Key Management Service"),
        ("LDAP", "Lightweight Directory Access Protocol"),
        ("MFA", "Multi-Factor Authentication"),
        ("mTLS", "Mutual TLS"),
        ("NACL", "Network ACL (AWS)"),
        ("NAT", "Network Address Translation"),
        ("NSG", "Network Security Group (Azure)"),
        ("OIDC", "OpenID Connect"),
        ("OPA", "Open Policy Agent"),
        ("OU", "Organizational Unit"),
        ("PAM", "Privileged Access Management"),
        ("PBAC", "Policy-Based Access Control"),
        ("PIM", "Privileged Identity Management (Azure)"),
        ("PSS", "Pod Security Standards"),
        ("RBAC", "Role-Based Access Control"),
        ("SAML", "Security Assertion Markup Language"),
        ("SCC", "Security Command Center (GCP)"),
        ("SCP", "Service Control Policy (AWS)"),
        ("SG", "Security Group (AWS)"),
        ("SIEM", "Security Info & Event Management"),
        ("SOAR", "Security Orchestration, Automation & Response"),
        ("SSE", "Server-Side Encryption"),
        ("SSO", "Single Sign-On"),
        ("STS", "Security Token Service (AWS)"),
        ("TLS", "Transport Layer Security"),
        ("VNet", "Virtual Network (Azure)"),
        ("VPC", "Virtual Private Cloud"),
        ("WAF", "Web Application Firewall"),
        ("ZTA", "Zero Trust Architecture"),
        ("ZTNA", "Zero Trust Network Access"),
    ]

    elements.append(make_table(
        ["Acronym", "Full Name"],
        [[a, n] for a, n in acronyms],
        col_widths=[1.0*inch, 5.5*inch]
    ))

    elements.append(PageBreak())
    return elements


def build_index_section(styles):
    """Build the master index section using tables for reliable rendering."""
    elements = []
    elements.append(Paragraph("MASTER INDEX", styles['SectionHeader']))
    elements.append(Paragraph(
        "Unified index (Clean + Missing Terms + Slide Keywords). "
        "Look up any term below to find the exact Book/Page in your SANS materials.",
        styles['BodyText8']
    ))
    elements.append(Spacer(1, 6))

    # Parse the master index file (merged from all three sources)
    index_path = REF_DIR / "SEC549_Master_Index.txt"
    if not index_path.exists():
        # Fallback to clean index if master not yet built
        index_path = REF_DIR / "SEC549_Clean_Index.txt"
    index_text = index_path.read_text(encoding="utf-8")

    # Styles for wrapping text inside table cells
    term_style = ParagraphStyle('idx_term', fontSize=6.5, leading=8, fontName='Helvetica-Bold')
    ref_style = ParagraphStyle('idx_ref', fontSize=6, leading=7.5, fontName='Helvetica')

    current_letter = None
    table_rows = []
    TABLE_CHUNK = 50  # Flush every N rows into a separate table

    def flush_table():
        nonlocal table_rows
        if not table_rows:
            return
        t = Table(table_rows, colWidths=[1.6*inch, 4.9*inch])
        t.setStyle(TableStyle([
            ('VALIGN', (0, 0), (-1, -1), 'TOP'),
            ('LEFTPADDING', (0, 0), (-1, -1), 2),
            ('RIGHTPADDING', (0, 0), (-1, -1), 2),
            ('TOPPADDING', (0, 0), (-1, -1), 0.5),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 0.5),
        ]))
        elements.append(t)
        table_rows = []

    for raw_line in index_text.split("\n"):
        line = raw_line.rstrip()
        stripped = line.strip()
        if not stripped:
            continue
        if stripped.startswith("===") or stripped.startswith("SEC549") or stripped.startswith("GIAC") or stripped.startswith("Format:") or stripped.startswith("CODE"):
            continue

        # Letter header
        letter_match = re.match(r'^-- ([A-Z#]) -+', stripped)
        if letter_match:
            letter = letter_match.group(1)
            if letter != current_letter:
                flush_table()
                current_letter = letter
                elements.append(Spacer(1, 4))
                elements.append(Paragraph(f"<b>--- {letter} ---</b>", styles['IndexLetter']))
            continue

        # Index entry - use Paragraph objects so long refs WRAP instead of clipping
        if raw_line.startswith("  ") and " > " in stripped:
            parts = stripped.split(" > ", 1)
            if len(parts) == 2:
                term, refs = parts
                table_rows.append([
                    Paragraph(escape_xml(term), term_style),
                    Paragraph(escape_xml(refs), ref_style),
                ])
                if len(table_rows) >= TABLE_CHUNK:
                    flush_table()

    flush_table()  # Final chunk
    return elements


def build_slide_keyword_index_section(styles):
    """Build the slide keyword index section."""
    elements = []
    elements.append(PageBreak())
    elements.append(Paragraph("SLIDE KEYWORD INDEX", styles['SectionHeader']))
    elements.append(Paragraph(
        "Terms extracted from slide titles and keywords across all 5 books. "
        "Use for quick topic-to-page lookup.",
        styles['BodyText8']
    ))
    elements.append(Spacer(1, 6))

    # Parse the slide keyword index file
    index_path = REF_DIR / "lastminGLossary" / "SEC549_Slide_Keywords_Index.txt"
    if not index_path.exists():
        elements.append(Paragraph("(Slide Keyword Index file not found)", styles['BodyText8']))
        return elements

    index_text = index_path.read_text(encoding="utf-8")

    term_style = ParagraphStyle('sk_term', fontSize=6.5, leading=8, fontName='Helvetica-Bold')
    ref_style = ParagraphStyle('sk_ref', fontSize=6, leading=7.5, fontName='Helvetica')

    current_letter = None
    table_rows = []
    TABLE_CHUNK = 50

    def flush_table():
        nonlocal table_rows
        if not table_rows:
            return
        t = Table(table_rows, colWidths=[2.8*inch, 3.7*inch])
        t.setStyle(TableStyle([
            ('VALIGN', (0, 0), (-1, -1), 'TOP'),
            ('LEFTPADDING', (0, 0), (-1, -1), 2),
            ('RIGHTPADDING', (0, 0), (-1, -1), 2),
            ('TOPPADDING', (0, 0), (-1, -1), 0.5),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 0.5),
        ]))
        elements.append(t)
        table_rows = []

    for raw_line in index_text.split("\n"):
        line = raw_line.rstrip()
        stripped = line.strip()
        if not stripped:
            continue
        if stripped.startswith("===") or stripped.startswith("SEC549") or stripped.startswith("GIAC") or stripped.startswith("Format:"):
            continue

        letter_match = re.match(r'^-- ([A-Z#]) -+', stripped)
        if letter_match:
            letter = letter_match.group(1)
            if letter != current_letter:
                flush_table()
                current_letter = letter
                elements.append(Spacer(1, 4))
                elements.append(Paragraph(f"<b>--- {letter} ---</b>", styles['IndexLetter']))
            continue

        if raw_line.startswith("  ") and " > " in stripped:
            parts = stripped.split(" > ", 1)
            if len(parts) == 2:
                term, refs = parts
                table_rows.append([
                    Paragraph(escape_xml(term), term_style),
                    Paragraph(escape_xml(refs), ref_style),
                ])
                if len(table_rows) >= TABLE_CHUNK:
                    flush_table()

    flush_table()
    return elements


def add_page_numbers(canvas, doc):
    """Add running headers and page numbers."""
    canvas.saveState()
    # Page number at bottom center
    canvas.setFont('Helvetica', 7)
    canvas.setFillColor(DARK_GRAY)
    canvas.drawCentredString(4.25 * inch, 0.4 * inch, f"SEC549 GIAC Exam Reference  |  Page {doc.page}")
    canvas.restoreState()


def main():
    print("=" * 60)
    print("CYRUS -- Phase D: Typesetting Print-Ready PDF")
    print("=" * 60)

    styles = get_styles()

    # Build document
    doc = SimpleDocTemplate(
        str(OUTPUT_PDF),
        pagesize=letter,
        leftMargin=0.75 * inch,  # Wider for spiral binding
        rightMargin=0.5 * inch,
        topMargin=0.6 * inch,
        bottomMargin=0.6 * inch,
    )

    elements = []

    # Assemble all sections
    print("  Building cover page...")
    elements.extend(build_cover_page(styles))

    print("  Building IAM section...")
    elements.extend(build_iam_section(styles))

    print("  Building Auth & Federation section...")
    elements.extend(build_auth_section(styles))

    print("  Building Network Security section...")
    elements.extend(build_network_section(styles))

    print("  Building Data Protection section...")
    elements.extend(build_data_section(styles))

    print("  Building Logging & Detection section...")
    elements.extend(build_logging_section(styles))

    print("  Building Zero Trust & Governance section...")
    elements.extend(build_zerotrust_section(styles))

    print("  Building Container Security section...")
    elements.extend(build_container_section(styles))

    print("  Building CLI Cheat Sheet...")
    elements.extend(build_cli_section(styles))

    print("  Building Acronym Glossary...")
    elements.extend(build_acronym_section(styles))

    print("  Building Master Index (this may take a moment)...")
    elements.extend(build_index_section(styles))

    # Generate PDF
    print("\n  Generating PDF...")
    doc.build(elements, onFirstPage=add_page_numbers, onLaterPages=add_page_numbers)

    print(f"  Saved: {OUTPUT_PDF}")
    print(f"  File size: {OUTPUT_PDF.stat().st_size / 1024:.0f} KB")

    print(f"\n{'=' * 60}")
    print("PHASE D COMPLETE")
    print(f"  Print-ready PDF: {OUTPUT_PDF.name}")
    print(f"  Ready for US Letter, spiral binding, color printing")
    print(f"{'=' * 60}")


if __name__ == "__main__":
    main()
