"""
Cyrus -- Phase B: Extract Content & Structure from SEC549 Books 1-5
Extracts topic structures, key terms, CLI commands, and builds topic-to-page mappings.
"""

import fitz  # PyMuPDF
import re
import json
from pathlib import Path
from collections import defaultdict

EXAM_DIR = Path(r"C:/Users/matth/Downloads/SEC549/Exam")
OUTPUT_DIR = EXAM_DIR

BOOK_FILES = [
    ("Book 1", EXAM_DIR / "SEC549 - Book 1_3355395_Decrypt.pdf"),
    ("Book 2", EXAM_DIR / "SEC549 - Book 2_3355395_Decrypt.pdf"),
    ("Book 3", EXAM_DIR / "SEC549 - Book 3_3355395_Decrypt.pdf"),
    ("Book 4", EXAM_DIR / "SEC549 - Book 4_3355395_Decrypt.pdf"),
    ("Book 5", EXAM_DIR / "SEC549 - Book 5_3355395_Decrypt.pdf"),
]


def extract_book_content(book_name, pdf_path):
    """Extract text, identify topics, commands, and key terms from a book."""
    doc = fitz.open(str(pdf_path))
    total_pages = len(doc)

    book_data = {
        "name": book_name,
        "total_pages": total_pages,
        "topics": [],           # major section topics
        "cli_commands": [],     # CLI commands found
        "key_terms": set(),     # important technical terms
        "cloud_services": set(),  # AWS/Azure/GCP service names
        "page_summaries": {},   # page -> brief content description
    }

    # Patterns for CLI command detection - require actual subcommands
    aws_subcommands = (
        "iam|sts|s3|s3api|ec2|lambda|cloudtrail|cloudwatch|kms|"
        "organizations|config|guardduty|securityhub|cognito-identity|"
        "cognito-idp|waf|wafv2|ssm|secretsmanager|cloudformation|"
        "eks|ecs|ecr|sns|sqs|rds|dynamodb|logs|events|route53|"
        "elbv2|autoscaling|macie2|inspector2|accessanalyzer|"
        "sso|sso-admin|identitystore|ram|shield"
    )
    az_subcommands = (
        "ad|account|aks|appservice|cosmosdb|functionapp|group|"
        "identity|keyvault|lock|monitor|network|policy|resource|"
        "role|security|sql|storage|vm|webapp|login|logout|"
        "deployment|container|acr|eventhub|servicebus|"
        "sentinel|defender|managed-identity"
    )
    gcloud_subcommands = (
        "iam|compute|container|kms|logging|monitoring|"
        "organizations|projects|storage|functions|run|"
        "dns|secrets|auth|config|services|artifacts|"
        "resource-manager|access-context-manager|"
        "identity|asset|scc"
    )

    # Only match actual lowercase CLI commands (not prose like "AWS IAM Identity Center")
    # Real CLI: aws iam list-users --profile prod
    # Not CLI: AWS IAM Identity Center is a service...
    cli_patterns = [
        rf'(aws\s+(?:{aws_subcommands})\s+[a-z][-a-z0-9]+(?:\s+[-][-]?\S+(?:\s+\S+)?)*)',
        rf'(az\s+(?:{az_subcommands})\s+[a-z][-a-z0-9]+(?:\s+[-][-]?\S+(?:\s+\S+)?)*)',
        rf'(gcloud\s+(?:{gcloud_subcommands})\s+[a-z][-a-z0-9]+(?:\s+[-][-]?\S+(?:\s+\S+)?)*)',
        r'(kubectl\s+(?:get|describe|apply|create|delete|exec|logs|port-forward|config|auth|rollout)\s+[a-z][-a-z0-9/.]+(?:\s+[-][-]?\S+(?:\s+\S+)?)*)',
        r'(terraform\s+(?:init|plan|apply|destroy|import|state|output|validate)\b(?:\s+[-][-]?\S+)*)',
        r'(curl\s+-[sSkXHdLvfI]+\s+\S+(?:\s+[-][-]?\S+(?:\s+\S+)?)*)',
    ]

    # Cloud service name patterns
    aws_services = [
        "IAM", "S3", "EC2", "Lambda", "CloudTrail", "CloudWatch", "VPC",
        "KMS", "STS", "Organizations", "Config", "GuardDuty", "SecurityHub",
        "CloudFormation", "EKS", "ECS", "ECR", "SNS", "SQS", "RDS",
        "DynamoDB", "Cognito", "WAF", "Shield", "Macie", "Inspector",
        "SSO", "Control Tower", "Service Control Policy", "SCP",
        "Permission Boundary", "Access Analyzer", "Secrets Manager",
        "Systems Manager", "Parameter Store", "CloudFront", "Route 53",
        "Transit Gateway", "PrivateLink", "Direct Connect", "EventBridge",
    ]
    azure_services = [
        "Entra ID", "Azure AD", "Active Directory", "Managed Identity",
        "Key Vault", "Storage Account", "Virtual Network", "NSG",
        "Application Gateway", "Front Door", "Defender for Cloud",
        "Sentinel", "Log Analytics", "Monitor", "Policy", "Blueprints",
        "Resource Manager", "RBAC", "Conditional Access", "PIM",
        "App Service", "Functions", "AKS", "Container Registry",
        "Private Endpoint", "Service Endpoint", "ExpressRoute",
        "Firewall", "DDoS Protection", "Bastion", "B2C", "B2B",
    ]
    gcp_services = [
        "Cloud IAM", "Cloud Storage", "Compute Engine", "Cloud Functions",
        "Cloud Run", "GKE", "Cloud KMS", "Cloud Audit Logs",
        "VPC Service Controls", "Cloud Armor", "Security Command Center",
        "Cloud Identity", "Workload Identity", "Binary Authorization",
        "Cloud HSM", "Secret Manager", "Organization Policy",
        "Cloud Interconnect", "Cloud VPN", "Cloud NAT", "Cloud DNS",
        "Artifact Registry", "Cloud Logging", "Cloud Monitoring",
    ]

    # Key security concepts to track
    security_concepts = [
        "zero trust", "least privilege", "defense in depth",
        "shared responsibility", "identity federation", "single sign-on",
        "multi-factor authentication", "MFA", "SAML", "OIDC", "OAuth",
        "JWT", "ABAC", "RBAC", "PBAC", "attribute-based",
        "role-based", "policy-based", "service account",
        "managed identity", "workload identity", "assume role",
        "cross-account", "privilege escalation", "lateral movement",
        "data exfiltration", "encryption at rest", "encryption in transit",
        "network segmentation", "microsegmentation", "peering",
        "private link", "service endpoint", "NAT gateway",
        "security group", "network ACL", "firewall rule",
        "audit log", "cloud trail", "flow log", "SIEM",
        "incident response", "compliance", "governance",
        "container security", "kubernetes security", "pod security",
        "infrastructure as code", "IaC", "CI/CD", "DevSecOps",
        "secret management", "key rotation", "certificate",
        "TLS", "SSL", "mutual TLS", "mTLS",
    ]

    all_text_by_page = {}

    for page_num in range(total_pages):
        page = doc[page_num]
        text = page.get_text("text")
        all_text_by_page[page_num + 1] = text

        # Extract CLI commands (case-sensitive - real CLI is lowercase)
        for pattern in cli_patterns:
            matches = re.findall(pattern, text)
            for match in matches:
                cmd = match.strip().replace('\n', ' ').replace('  ', ' ')
                if len(cmd) > 10:
                    book_data["cli_commands"].append({
                        "command": cmd,
                        "page": page_num + 1,
                    })

        # Track cloud services mentioned
        for svc in aws_services:
            if svc.lower() in text.lower():
                book_data["cloud_services"].add(f"AWS: {svc}")
        for svc in azure_services:
            if svc.lower() in text.lower():
                book_data["cloud_services"].add(f"Azure: {svc}")
        for svc in gcp_services:
            if svc.lower() in text.lower():
                book_data["cloud_services"].add(f"GCP: {svc}")

        # Track security concepts
        for concept in security_concepts:
            if concept.lower() in text.lower():
                book_data["key_terms"].add(concept)

    doc.close()

    # Detect topic structure from text patterns
    # SANS slides often have section titles in larger fonts or specific patterns
    topics = detect_topics(all_text_by_page)
    book_data["topics"] = topics

    # Convert sets to sorted lists for JSON serialization
    book_data["cloud_services"] = sorted(list(book_data["cloud_services"]))
    book_data["key_terms"] = sorted(list(book_data["key_terms"]))

    # Deduplicate CLI commands
    seen_cmds = set()
    unique_cmds = []
    for cmd in book_data["cli_commands"]:
        key = cmd["command"][:50]  # dedupe on first 50 chars
        if key not in seen_cmds:
            seen_cmds.add(key)
            unique_cmds.append(cmd)
    book_data["cli_commands"] = unique_cmds

    return book_data


def detect_topics(pages_text):
    """Try to detect major topics/sections from page text."""
    topics = []

    for page_num, text in pages_text.items():
        lines = text.strip().split("\n")
        for line in lines[:5]:  # Check first few lines of each page
            line = line.strip()
            # Look for section-like patterns:
            # - Lines that are short (< 80 chars), title-case or all caps
            # - Lines starting with "Section", "Module", numbers like "1.", "2."
            if not line or len(line) > 100 or len(line) < 3:
                continue

            # Numbered sections
            section_match = re.match(r'^(?:Section|Module|Chapter|Lab)?\s*(\d+[\.:]\s*.+)', line, re.IGNORECASE)
            if section_match and len(line) < 80:
                topics.append({"title": line.strip(), "page": page_num})
                continue

            # Title-case lines that look like section headers (short, no period at end)
            if (line.istitle() or line.isupper()) and len(line) > 5 and len(line) < 60 and not line.endswith('.'):
                # Filter out common non-header patterns
                skip_words = ["sans", "sec549", "copyright", "all rights", "page"]
                if not any(sw in line.lower() for sw in skip_words):
                    topics.append({"title": line.strip(), "page": page_num})

    return topics


def build_topic_map(all_books_data):
    """Build a consolidated topic-to-book-page mapping."""
    topic_map = {}
    for book in all_books_data:
        book_name = book["name"]
        topic_map[book_name] = {
            "pages": book["total_pages"],
            "cloud_services": book["cloud_services"],
            "key_terms": book["key_terms"],
            "topics": book["topics"][:30],  # Top 30 topics per book
            "cli_commands_count": len(book["cli_commands"]),
        }
    return topic_map


def main():
    print("=" * 60)
    print("CYRUS -- Phase B: Content Extraction from Books 1-5")
    print("=" * 60)

    all_books = []

    for book_name, pdf_path in BOOK_FILES:
        print(f"\n[{book_name}] Extracting from: {pdf_path.name}")
        if not pdf_path.exists():
            print(f"  WARNING: File not found, skipping")
            continue

        data = extract_book_content(book_name, pdf_path)
        all_books.append(data)

        print(f"  Pages: {data['total_pages']}")
        print(f"  Topics detected: {len(data['topics'])}")
        print(f"  CLI commands: {len(data['cli_commands'])}")
        print(f"  Cloud services: {len(data['cloud_services'])}")
        print(f"  Key concepts: {len(data['key_terms'])}")

    # Save individual book extractions
    for book_data in all_books:
        fname = f"SEC549_{book_data['name'].replace(' ', '_')}_Extract.json"
        out_path = OUTPUT_DIR / fname
        with open(out_path, "w", encoding="utf-8") as f:
            json.dump(book_data, f, indent=2, ensure_ascii=False)
        print(f"\n  Saved: {out_path.name}")

    # Build consolidated topic map
    topic_map = build_topic_map(all_books)
    map_path = OUTPUT_DIR / "SEC549_Topic_Map.json"
    with open(map_path, "w", encoding="utf-8") as f:
        json.dump(topic_map, f, indent=2, ensure_ascii=False)
    print(f"\n  Topic map: {map_path.name}")

    # Build consolidated CLI command reference
    all_commands = []
    for book_data in all_books:
        for cmd in book_data["cli_commands"]:
            all_commands.append({
                "book": book_data["name"],
                "page": cmd["page"],
                "command": cmd["command"],
            })

    cmd_path = OUTPUT_DIR / "SEC549_CLI_Commands.json"
    with open(cmd_path, "w", encoding="utf-8") as f:
        json.dump(all_commands, f, indent=2, ensure_ascii=False)
    print(f"  CLI commands: {cmd_path.name} ({len(all_commands)} total)")

    # Build cloud services cross-reference
    services_by_provider = {"AWS": set(), "Azure": set(), "GCP": set()}
    for book_data in all_books:
        for svc in book_data["cloud_services"]:
            provider, name = svc.split(": ", 1)
            services_by_provider[provider].add(name)

    svc_path = OUTPUT_DIR / "SEC549_Cloud_Services.json"
    svc_data = {k: sorted(list(v)) for k, v in services_by_provider.items()}
    with open(svc_path, "w", encoding="utf-8") as f:
        json.dump(svc_data, f, indent=2, ensure_ascii=False)
    print(f"  Cloud services: {svc_path.name}")

    # Summary
    print(f"\n{'=' * 60}")
    print("PHASE B SUMMARY")
    total_pages = sum(b["total_pages"] for b in all_books)
    total_cmds = len(all_commands)
    total_svcs = sum(len(v) for v in services_by_provider.values())
    print(f"  Total pages across 5 books: {total_pages}")
    print(f"  Total CLI commands found:   {total_cmds}")
    print(f"  Total cloud services found: {total_svcs}")
    for provider, svcs in sorted(svc_data.items()):
        print(f"    {provider}: {len(svcs)} services")
    print(f"{'=' * 60}")


if __name__ == "__main__":
    main()
