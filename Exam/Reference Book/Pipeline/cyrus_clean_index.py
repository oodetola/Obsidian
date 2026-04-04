"""
Cyrus -- Phase A v3: Omega Index Cleanup Pipeline (Enhanced)
SEC549 GIAC Exam Reference Book

Improvements over v2:
1. Dictionary-based validation via symspellpy (replaces heuristic-only scoring)
2. Junk suffix stripping pre-pass (rrrcmmk, bedccc, fabedccc, yuebzyqemvasrrrcmmk)
3. Removed same-first-letter constraint on fuzzy matching
4. Underscore-prefix handling
5. Domain-specific technical glossary whitelist
6. Better garbled detection that doesn't flag real crypto/security terms
"""

import re
import sys
import json
from collections import defaultdict
from pathlib import Path
from rapidfuzz import fuzz
import symspellpy
import jellyfish

# Force UTF-8 output on Windows
sys.stdout.reconfigure(encoding="utf-8")

# --- Configuration ---

INPUT_FILE = Path(r"C:/Users/matth/Downloads/SEC549/Exam/tabbed SANS book/omegaindex_549.txt")
REF_DIR = Path(r"C:/Users/matth/Downloads/SEC549/Exam/Reference Book")
OUTPUT_DIR = REF_DIR
DATA_DIR = REF_DIR / "Data"
FUZZY_THRESHOLD = 75  # Slightly more aggressive (was 78)
MAX_USEFUL_PAGES = 60

# --- Known junk suffixes (recurring OCR garbage tails) ---
JUNK_SUFFIXES = [
    "yuebzyqemvasrrrcmmk",
    "bzyqemvasrrrcmmk",
    "qemvasrrrcmmk",
    "asrrrcmmk",
    "srrrcmmk",
    "rrrcmmk",
    "rcmmk",
    "cmmk",
    "fabedccc",
    "bedccc",
    "edccc",
    "dccc",
]

# --- Stop words ---
STOP_WORDS = {
    "a", "an", "the", "and", "or", "but", "in", "on", "at", "to", "for",
    "of", "with", "by", "from", "is", "it", "its", "as", "be", "was",
    "are", "were", "been", "has", "have", "had", "do", "does", "did",
    "will", "would", "could", "should", "may", "might", "can", "shall",
    "not", "no", "so", "if", "then", "than", "that", "this", "these",
    "those", "which", "what", "who", "whom", "where", "when", "how",
    "all", "each", "every", "both", "few", "more", "most", "other",
    "some", "such", "only", "own", "same", "also", "into", "over",
    "after", "before", "between", "through", "during", "about", "above",
    "below", "up", "down", "out", "off", "here", "there", "just",
    "very", "too", "any", "many", "much", "well", "still", "even",
    "now", "new", "old", "way", "like", "use", "used", "using",
    "see", "set", "get", "let", "one", "two", "make", "made",
    "need", "must", "sure", "note", "next", "step", "first", "last",
    "while", "because", "since", "until", "although", "though",
    "however", "therefore", "thus", "hence", "yet", "already",
    "we", "you", "they", "he", "she", "me", "us", "them", "our",
    "your", "their", "my", "his", "her", "i", "being", "another",
    "once", "again", "further", "don", "doesn", "didn", "won", "wouldn",
    "couldn", "shouldn", "isn", "aren", "wasn", "weren", "hasn", "haven",
    "hadn", "ll", "ve", "re", "able", "within", "without",
    "shown", "shows", "show", "right", "left",
    "click", "page", "slide", "figure", "book", "section",
}

# --- Domain-specific technical terms whitelist ---
# These MUST survive any dictionary check or garbled detection
TECHNICAL_TERMS = {
    # Cloud providers & services
    "aws", "azure", "gcp", "iam", "ec2", "ebs", "eks", "ecs", "rds", "vpc", "vpn",
    "s3", "sqs", "sns", "arn", "ami", "acl", "alb", "nlb", "elb", "nat", "igw",
    "cloudtrail", "cloudwatch", "cloudformation", "cloudfront", "cloudflare",
    "cognito", "guardduty", "macie", "securityhub", "sso", "sts", "kms", "hsm",
    "lambda", "fargate", "terraform", "ansible", "kubernetes", "k8s", "kubectl",
    "docker", "helm", "istio", "envoy", "calico", "falco", "gke", "aks", "oke",
    "entra", "sentinel", "defender", "intune", "purview", "bicep",
    "bigquery", "gcs", "gcr", "pub/sub", "anthos",
    # Security terms
    "saml", "oidc", "oauth", "jwt", "jws", "jwk", "jwks", "mfa", "totp", "fido2",
    "rbac", "abac", "pbac", "xacml", "spiffe", "spire", "mtls", "tls", "ssl",
    "ssh", "pki", "ca", "crl", "ocsp", "x509", "pkcs", "hmac", "sha", "rsa",
    "aes", "ecdsa", "ed25519", "opaque", "scram",
    "siem", "soar", "xdr", "edr", "ndr", "dlp", "casb", "cspm", "cwpp", "cnapp",
    "ciem", "sase", "ztna", "sdp", "waf", "ips", "ids", "nac", "hids", "nids",
    "scp", "ou", "gpo", "ldap", "ntlm", "ntds", "sam", "sid", "guid", "uuid",
    "cidr", "dns", "dhcp", "icmp", "tcp", "udp", "http", "https", "grpc", "rest",
    "api", "sdk", "cli", "iac", "sdlc", "devsecops", "sast", "dast", "iast", "sca",
    "cve", "cvss", "epss", "cwe", "capec", "stix", "taxii", "mitre",
    "nist", "iso", "soc2", "pci", "hipaa", "gdpr", "ccpa", "fedramp", "fisma",
    "owasp", "sans", "cis", "disa", "stig",
    "csrf", "xss", "xxe", "ssrf", "sqli", "rce", "lfi", "rfi", "idor",
    "apt", "c2", "ioc", "ttp", "yara", "sigma", "suricata", "snort", "zeek",
    "osint", "humint", "sigint", "socmint",
    "ransomware", "malware", "phishing", "spearphishing", "rootkit", "botnet",
    "keylogger", "trojan", "worm", "backdoor", "webshell", "cryptominer",
    # Crypto & security terms that look like garbage to naive checkers
    "crypto", "cryptographic", "cryptographically", "cryptography", "cryptosystem",
    "encrypt", "encrypted", "encryption", "decrypt", "decrypted", "decryption",
    "ciphertext", "plaintext", "nonce", "salt", "hash", "hashing",
    # Infrastructure
    "mysql", "postgresql", "mssql", "nosql", "mongodb", "redis", "elasticsearch",
    "kafka", "nginx", "apache", "haproxy", "consul", "vault", "nomad",
    "grafana", "prometheus", "datadog", "splunk", "logstash", "kibana",
    "jenkins", "gitlab", "github", "circleci", "argocd", "fluxcd",
    # Common technical terms
    "async", "sync", "webhook", "websocket", "microservice", "monolith",
    "json", "yaml", "xml", "csv", "protobuf", "avro", "parquet",
    "regex", "glob", "cron", "etcd", "grub", "uefi", "bios",
    "cfssl", "openssl", "certbot", "acme",
    "mpls", "bgp", "ospf", "vlan", "vxlan", "geneve", "wireguard",
    "ipv4", "ipv6", "ipam", "fqdn", "ttl", "soa", "cname", "ptr",
    "scada", "plc", "hmi", "ics", "ot", "modbus", "dnp3",
    # Misc that might look garbled
    "appscripts", "vpcflow", "right-click",
    "symptom", "synchronously", "asynchronously", "lengths", "rhythm",
    # Common security/exam terms that must survive filters
    "policy", "policies", "principal", "principals", "permission", "permissions",
    "analyst", "analysts", "compliance", "governance", "assessment",
    "vulnerability", "vulnerabilities", "remediation", "mitigation",
    "incident", "response", "forensics", "investigation",
    "captcha", "recaptcha", "oauth2", "openid",
    "account", "accounts", "access", "identity", "identities",
    "resource", "resources", "service", "services", "endpoint", "endpoints",
    "cluster", "clusters", "container", "containers", "workload", "workloads",
    "namespace", "namespaces", "deployment", "deployments",
    "firewall", "firewalls", "gateway", "gateways", "proxy", "proxies",
    "subnet", "subnets", "peering", "transit", "express",
    "tenant", "tenants", "subscription", "subscriptions", "organization", "organizations",
    "role", "roles", "group", "groups", "user", "users",
    "secret", "secrets", "certificate", "certificates", "credential", "credentials",
    "token", "tokens", "session", "sessions", "cookie", "cookies",
    "logging", "monitoring", "alerting", "auditing", "tracing",
    "bucket", "buckets", "blob", "blobs", "queue", "queues",
    "registry", "registries", "repository", "repositories",
    "encryption", "rotation", "expiration", "revocation",
    "federation", "delegation", "impersonation", "escalation",
    "boundary", "boundaries", "perimeter", "segment", "segmentation",
    "baseline", "benchmark", "standard", "framework", "control", "controls",
    "available", "availability", "resiliency", "redundancy",
    # Path-like terms that are real
    "vpc/shared", "vpc/vnet", "https/tls", "encrypt/decrypt", "mpls/direct",
    # Product/service names not in English dictionary
    "vmware", "okta", "onedrive", "opensearch", "orangehrm", "cloudockit",
    "dynamodb", "kinesis", "cognito", "fargate", "athena", "redshift",
    "snowflake", "databricks", "datadog", "crowdstrike", "tenable",
    "qualys", "nessus", "prisma", "zscaler", "cloudflare", "akamai",
    "pagerduty", "opsgenie", "servicenow", "jira", "confluence",
    "bitbucket", "codecommit", "codepipeline", "codebuild",
    "cloudshell", "powershell", "kubectl", "eksctl", "awscli",
    "boto3", "gcloud", "azurecli", "pulumi", "crossplane",
    "istio", "linkerd", "envoy", "calico", "cilium", "falco",
    "trivy", "aqua", "snyk", "sonarqube", "checkmarx", "veracode",
    "keycloak", "auth0", "pingidentity", "forgerock", "cyberark",
    "hashicorp", "infoblox", "netskope", "crowdstrike", "sentinelone",
    "wiz", "orca", "lacework", "sysdig", "twistlock",
    "dodaf", "togaf", "sabsa", "cobit", "itil",
}

# Build lowercase set for fast lookup
TECHNICAL_TERMS_LOWER = {t.lower() for t in TECHNICAL_TERMS}


# --- Initialize symspellpy dictionary ---
def init_spell_checker():
    """Load symspellpy with English frequency dictionary."""
    sym = symspellpy.SymSpell(max_dictionary_edit_distance=2, prefix_length=7)
    pkg_dir = Path(symspellpy.__file__).parent
    dict_path = pkg_dir / "frequency_dictionary_en_82_765.txt"
    if dict_path.exists():
        sym.load_dictionary(str(dict_path), term_index=0, count_index=1)
    else:
        print(f"  WARNING: Dictionary not found at {dict_path}")
    # Add our technical terms to the dictionary
    for term in TECHNICAL_TERMS_LOWER:
        sym.create_dictionary_entry(term, 1000)
    return sym


# --- Step 0: Junk suffix stripping ---
def strip_junk_suffix(term):
    """Strip known OCR junk suffixes from terms. Returns (cleaned_term, was_stripped)."""
    t = term
    for suffix in JUNK_SUFFIXES:
        if t.lower().endswith(suffix) and len(t) > len(suffix):
            stripped = t[:-len(suffix)]
            # Only strip if what remains looks meaningful (>= 2 chars)
            if len(stripped.strip()) >= 2:
                return stripped.strip(), True
    return t, False


# --- Step 1: Parse ---
def parse_omega_index(filepath):
    entries = {}
    raw_lines = filepath.read_text(encoding="utf-8").strip().splitlines()
    for line in raw_lines:
        line = line.strip()
        if not line:
            continue
        match = re.match(r'^(.+?):\s+(.+)$', line)
        if not match:
            continue
        term = match.group(1).strip()
        refs_str = match.group(2).strip()
        book_pages = defaultdict(set)
        current_book = None
        for token in re.split(r'[\s,]+', refs_str):
            token = token.strip()
            if not token:
                continue
            book_match = re.match(r'\((\d)\)(-?\d+)', token)
            if book_match:
                current_book = int(book_match.group(1))
                page = int(book_match.group(2))
                book_pages[current_book].add(page)
            elif current_book is not None and re.match(r'^-?\d+$', token):
                book_pages[current_book].add(int(token))
        if book_pages:
            entries[term] = {b: sorted(list(p)) for b, p in book_pages.items()}
    return entries


# --- Step 2: Classify ---
def is_code_or_path(term):
    """Code snippets, paths, variables, URLs -- keep as-is."""
    if any(term.startswith(c) for c in ['$', '.', '/', '<', '>', '{', '|', '~', '*', '#']):
        return True
    if '(' in term and ')' in term and any(c in term for c in ['.', '_']):
        return True  # function calls
    # dotted.names — but validate both parts look like real identifiers
    # (not garbled OCR like "odirectdory.e" or "ormganizaationt.tbhelowe")
    m = re.match(r'^([a-z_]+)\.([a-z_]+)$', term)
    if m:
        left, right = m.group(1), m.group(2)
        # Real dotted names: both parts >=2 chars and no 4+ consonant runs
        if (len(left) >= 2 and len(right) >= 2 and
            not re.search(r'[bcdfghjklmnpqrstvwxyz]{4}', left) and
            not re.search(r'[bcdfghjklmnpqrstvwxyz]{4}', right)):
            return True
    # Multi-segment dotted paths (3+ segments like a.b.c) — likely real code
    if re.match(r'^[a-z_]+(\.[a-z_]+){2,}', term):
        return True
    return False


def is_page_zero_only(refs):
    all_pages = []
    for pages in refs.values():
        all_pages.extend(pages)
    return all(p <= 0 for p in all_pages)


# --- Step 3: Dictionary-based validation ---
def is_real_word(term, spell_checker):
    """Check if a term is a real English word or close to one using symspellpy."""
    t = term.lower().strip()

    # Direct match in technical terms
    if t in TECHNICAL_TERMS_LOWER:
        return True

    # Check hyphenated terms
    if '-' in t or '/' in t:
        parts = re.split(r'[-/]', t)
        # If most parts are real words, the term is probably real
        real_parts = sum(1 for p in parts if p and (
            p in TECHNICAL_TERMS_LOWER or
            len(spell_checker.lookup(p, symspellpy.Verbosity.CLOSEST, max_edit_distance=0)) > 0
        ))
        if real_parts >= len([p for p in parts if p]) * 0.6:
            return True

    # Check with spell checker (exact match)
    results = spell_checker.lookup(t, symspellpy.Verbosity.CLOSEST, max_edit_distance=0)
    if results:
        return True

    # Check with edit distance 1 (close to a real word)
    results = spell_checker.lookup(t, symspellpy.Verbosity.CLOSEST, max_edit_distance=1)
    if results and results[0].distance <= 1:
        return True

    return False


def is_compound_valid(term, spell_checker):
    """Check if a compound term (hyphenated/slashed) decomposes into known parts."""
    parts = re.split(r'[-/,:]', term.lower())
    parts = [p for p in parts if p and len(p) > 0]
    if not parts:
        return False
    valid = 0
    for p in parts:
        if p in TECHNICAL_TERMS_LOWER:
            valid += 1
        elif len(p) <= 2:
            valid += 1  # short connectors like "to", "as", "a"
        elif spell_checker.lookup(p, symspellpy.Verbosity.CLOSEST, max_edit_distance=0):
            valid += 1
        elif spell_checker.lookup(p, symspellpy.Verbosity.CLOSEST, max_edit_distance=1):
            valid += 0.5
    return valid >= len(parts) * 0.5


def is_garbled(term, spell_checker):
    """Determine if a term is OCR garbage. Returns True if garbage.

    Strategy: dictionary validation is PRIMARY. If a term is a known word or
    decomposes into known parts, it survives. Unknown terms must pass
    heuristic checks to survive.
    """
    t = term.lower().strip()

    # --- Layer 1: Whitelists (never flag) ---

    if t in TECHNICAL_TERMS_LOWER:
        return False

    # Compound terms (hyphenated/slashed/colon) — check parts
    if any(c in t for c in ['-', '/', ':']):
        if is_compound_valid(term, spell_checker):
            return False

    alpha = re.sub(r'[^a-z]', '', t)
    if not alpha or len(alpha) < 3:
        return False

    # Exact dictionary word — never flag
    if spell_checker.lookup(t, symspellpy.Verbosity.CLOSEST, max_edit_distance=0):
        return False

    # --- Early hard rules (before d=1 pass) ---

    # "ohn" prefix pattern = garbled "on" (extremely common OCR artifact)
    if alpha.startswith('ohn') and len(alpha) >= 3:
        return True

    # Contains known junk substrings
    if re.search(r'(rrrcmmk|yuebzyqemvasrrrcmmk|bedccc|fabedccc|bzyqemvasrrrcmmk|qemvasrrrcmmk)', t):
        return True

    # Within edit distance 1 of a dictionary word — usually pass, UNLESS the term
    # looks like a garbled version (extra char prepended/appended to a common word)
    confirmed_nonword = False  # Track if this is a confirmed non-dictionary term
    r1 = spell_checker.lookup(t, symspellpy.Verbosity.CLOSEST, max_edit_distance=1)
    if r1 and r1[0].distance <= 1:
        closest = r1[0].term
        # Term is NOT in dictionary (d=0 failed above). If it's short, it's garbled.
        # Real 3-5 letter English words are always in the 82K dictionary.
        if len(alpha) <= 5:
            return True
        # For 6+ char terms: if term is longer than closest = extra chars inserted
        if len(t) > len(closest):
            confirmed_nonword = True
            if closest in STOP_WORDS:
                return True
            if len(alpha) <= 7:
                return True
            # Longer terms: continue to garbled checks
        else:
            return False  # Same length or shorter, 6+ chars = likely legitimate variant

    # --- Layer 2: Hard garbage rules (always flag) ---

    # "ohn" prefix pattern = garbled "on" (extremely common OCR artifact)
    if alpha.startswith('ohn') and len(alpha) >= 4:
        return True

    # Contains known junk substrings
    if re.search(r'(rrrcmmk|yuebzyqemvasrrrcmmk|bedccc|fabedccc|bzyqemvasrrrcmmk|qemvasrrrcmmk)', t):
        return True

    # Triple+ repeated characters
    if re.search(r'(.)\1{2,}', alpha):
        return True

    # Extremely long with no vowels
    if len(alpha) > 8 and sum(1 for c in alpha if c in 'aeiou') == 0:
        return True

    max_consonants = max((len(m) for m in re.findall(r'[^aeiou]+', alpha)), default=0)
    if max_consonants >= 6:
        return True

    # Contains embedded punctuation in odd places (commas, quotes inside words)
    if re.search(r'[a-z][,"\'][a-z]', t) and not any(c in t for c in ['-', '/', ':']):
        return True

    # --- Layer 3: Unknown word analysis ---
    # Term is NOT in dictionary, NOT a technical term, NOT a valid compound.
    # Now decide: is it a legitimate unknown word or garbled?

    vowels = sum(1 for c in alpha if c in 'aeiou')
    vowel_ratio = vowels / len(alpha) if alpha else 0

    # Check if it's within edit distance 2 of ANY word
    r2 = spell_checker.lookup(t, symspellpy.Verbosity.CLOSEST, max_edit_distance=2)

    # Short unknown terms (3-6 chars): NOT in dictionary at d=0 = garbled.
    # Real short English words are always in the 82K dictionary.
    if len(alpha) <= 6:
        return True

    # Single unknown words > 6 chars that aren't close to any dictionary word = garbage
    if len(alpha) > 6 and not r2:
        return True

    # Non-dictionary term at d=2 whose closest match has a different first letter = garbled OCR
    # (real words don't randomly change their starting letter)
    if r2 and r2[0].distance == 2 and len(alpha) > 0:
        closest = r2[0].term
        if closest and alpha[0] != closest[0]:
            return True

    # Single unknown words > 6 chars that are d=2 from a word = suspicious
    # Flag if they also have heuristic garbage signals
    garbage_signals = 0

    if vowel_ratio < 0.2 and len(alpha) > 5:
        garbage_signals += 2
    elif vowel_ratio < 0.25 and len(alpha) > 6:
        garbage_signals += 1

    if len(alpha) > 3 and alpha[0] == alpha[1]:
        garbage_signals += 1

    zq_count = alpha.count('z') + alpha.count('q')
    if len(alpha) > 5 and zq_count / len(alpha) > 0.15:
        garbage_signals += 1

    if max_consonants >= 5:
        garbage_signals += 1
    elif max_consonants >= 4 and len(alpha) > 6:
        garbage_signals += 1

    if re.search(r'[bcdfghjklmnpqrstvwxyz]{4}', alpha):
        garbage_signals += 1

    # Unknown word with garbage signals = garbage
    if garbage_signals >= 1 and not r2:
        return True

    if garbage_signals >= 2:
        return True

    # --- Layer 4: Interleaved-character OCR detection ---
    # Garbled terms like "ohnaccerss" (on access), "tpraincinpal" (principal)
    # These are d=2 from a real word but longer (extra chars inserted)

    if len(alpha) > 6 and r2:
        closest = r2[0].term
        # If the garbled term is significantly longer than its closest match,
        # extra characters were inserted = OCR artifact
        if len(alpha) > len(closest) + 2 and r2[0].distance == 2:
            return True

    # --- Layer 5: Prepended/appended char artifacts ---
    # "mpolicya" = 'm' + 'policy' + 'a'
    if len(alpha) >= 5:
        inner = alpha[1:-1]
        if len(inner) >= 3:
            if inner in STOP_WORDS or inner in TECHNICAL_TERMS_LOWER:
                return True
            if spell_checker.lookup(inner, symspellpy.Verbosity.CLOSEST, max_edit_distance=0):
                return True
        if alpha[1:] in STOP_WORDS:
            return True
        if alpha[:-1] in STOP_WORDS:
            return True

    return False


def cleanliness_score(term, spell_checker=None):
    """Score how likely a term is to be a real word (higher = cleaner). Range: 0-100."""
    t = term.lower().strip()

    # Technical term = definitely clean
    if t in TECHNICAL_TERMS_LOWER:
        return 100

    # Check hyphenated combo of known terms
    parts = re.split(r'[-/]', t)
    if len(parts) > 1 and all(p in TECHNICAL_TERMS_LOWER or len(p) <= 2 for p in parts if p):
        return 95

    # Dictionary word = clean
    if spell_checker:
        results = spell_checker.lookup(t, symspellpy.Verbosity.CLOSEST, max_edit_distance=0)
        if results:
            return 90

    alpha = re.sub(r'[^a-z]', '', t)
    if not alpha or len(alpha) < 2:
        return 50

    score = 70  # baseline

    # Penalize: starts with doubled letter
    if len(alpha) > 2 and alpha[0] == alpha[1]:
        score -= 15

    # Penalize: excessive consecutive consonants
    max_consonants = max((len(m) for m in re.findall(r'[^aeiou]+', alpha)), default=0)
    if max_consonants >= 5:
        score -= 20
    elif max_consonants >= 4:
        score -= 10

    # Penalize: very high consonant-to-vowel ratio
    vowels = sum(1 for c in alpha if c in 'aeiou')
    if len(alpha) > 4 and vowels / len(alpha) < 0.2:
        score -= 20

    # Penalize: triple+ repeated chars
    if re.search(r'(.)\1{2,}', alpha):
        score -= 30

    # Penalize: random z/q insertions
    z_count = alpha.count('z') + alpha.count('q')
    if len(alpha) > 5 and z_count / len(alpha) > 0.15:
        score -= 15

    # Reward: ends in common English suffixes
    suffixes = ('tion', 'sion', 'ment', 'ness', 'able', 'ible', 'ity', 'ous',
                'ive', 'ing', 'ated', 'ized', 'ally', 'ful', 'less', 'ence', 'ance')
    if any(alpha.endswith(s) for s in suffixes):
        score += 10

    # Reward: dictionary match within edit distance 1
    if spell_checker:
        results = spell_checker.lookup(t, symspellpy.Verbosity.CLOSEST, max_edit_distance=1)
        if results and results[0].distance <= 1:
            score += 15

    return max(0, min(100, score))


# --- Step 4: Cluster & merge ---
def merge_refs(ref1, ref2):
    merged = defaultdict(set)
    for book, pages in ref1.items():
        merged[book].update(pages)
    for book, pages in ref2.items():
        merged[book].update(pages)
    return {b: sorted(list(p)) for b, p in merged.items()}


def cluster_and_merge(entries, spell_checker, threshold=FUZZY_THRESHOLD):
    """Cluster similar entries, pick cleanest as canonical, merge page refs.
    No longer requires same first letter for fuzzy matching.
    Technical terms always win as canonical."""
    terms = list(entries.keys())
    # Sort: technical terms first (score 100+), then by cleanliness
    def sort_key(t):
        is_tech = 1000 if t.lower().strip() in TECHNICAL_TERMS_LOWER else 0
        return -(is_tech + cleanliness_score(t, spell_checker)), t
    terms.sort(key=sort_key)

    merged = {}
    consumed = set()

    # Build a simple index by first 2 chars for faster lookup
    # But also check across similar starting chars
    char_index = defaultdict(list)
    for t in terms:
        if t:
            char_index[t[0].lower()].append(t)
            # Also index by the char the term WOULD start with if first char is doubled OCR artifact
            alpha = re.sub(r'[^a-z]', '', t.lower())
            if len(alpha) > 2 and alpha[0] == alpha[1]:
                char_index[alpha[1]].append(t)

    for term in terms:
        if term in consumed:
            continue

        canonical = term
        canonical_refs = dict(entries[term])
        canonical_score = cleanliness_score(term, spell_checker)

        # Find similar terms - check same first letter AND doubled-letter variants
        first_char = term[0].lower() if term else ''
        candidates = set()

        # Same first letter
        for t in char_index.get(first_char, []):
            if t not in consumed and t != term:
                candidates.add(t)

        # Also check if this term's de-doubled first letter matches others
        alpha = re.sub(r'[^a-z]', '', term.lower())
        if len(alpha) > 2 and alpha[0] == alpha[1]:
            for t in char_index.get(alpha[1], []):
                if t not in consumed and t != term:
                    candidates.add(t)

        for candidate in candidates:
            score = fuzz.ratio(term.lower(), candidate.lower())
            if score >= threshold:
                cand_is_tech = candidate.lower().strip() in TECHNICAL_TERMS_LOWER
                canon_is_tech = canonical.lower().strip() in TECHNICAL_TERMS_LOWER

                # NEVER merge two different technical terms — they are distinct entries
                if cand_is_tech and canon_is_tech:
                    continue

                # Don't merge two different EXACT dictionary words
                # (prevents merging "authenticate" into "authentication")
                cand_exact = len(spell_checker.lookup(candidate.lower().strip(),
                    symspellpy.Verbosity.CLOSEST, max_edit_distance=0)) > 0 or cand_is_tech
                canon_exact = len(spell_checker.lookup(canonical.lower().strip(),
                    symspellpy.Verbosity.CLOSEST, max_edit_distance=0)) > 0 or canon_is_tech
                if cand_exact and canon_exact and \
                   candidate.lower().strip() != canonical.lower().strip():
                    continue

                cand_score = cleanliness_score(candidate, spell_checker)
                # Technical terms always win as canonical
                if (cand_is_tech and not canon_is_tech) or \
                   (cand_is_tech == canon_is_tech and cand_score > canonical_score):
                    canonical = candidate
                    canonical_score = cand_score
                canonical_refs = merge_refs(canonical_refs, entries[candidate])
                consumed.add(candidate)

        merged[canonical] = canonical_refs
        consumed.add(term)

    return merged


# --- Step 5: Final filtering ---
def total_page_count(refs):
    return sum(len(pages) for pages in refs.values())


def final_filter(entries, spell_checker):
    """Remove stop words, garbled entries, and low-value entries."""
    filtered = {}
    removed_stops = 0
    removed_garbage = 0
    removed_high_count = 0
    removed_garbled = 0
    garbage_log = []

    for term, refs in entries.items():
        t = term.lower().strip()
        clean_alpha = re.sub(r'[^a-z]', '', t)

        # Remove stop words
        if clean_alpha in STOP_WORDS:
            removed_stops += 1
            continue

        # Remove garbled entries (dictionary-enhanced)
        if not is_code_or_path(term) and is_garbled(term, spell_checker):
            removed_garbled += 1
            garbage_log.append(f"  [garbled] {term}")
            continue

        # Remove entries with very low cleanliness that aren't code
        if not is_code_or_path(term) and cleanliness_score(term, spell_checker) < 20:
            removed_garbage += 1
            garbage_log.append(f"  [low_quality] {term}")
            continue

        # Filter out page 0 refs
        clean_refs = {}
        for book, pages in refs.items():
            non_zero = [p for p in pages if p > 0]
            if non_zero:
                clean_refs[book] = non_zero

        if not clean_refs:
            garbage_log.append(f"  [page_zero_only] {term}")
            continue

        # Remove single-char and two-char non-technical terms (not useful in exam)
        if len(clean_alpha) <= 2 and clean_alpha not in TECHNICAL_TERMS_LOWER:
            removed_stops += 1
            continue

        # Remove entries appearing on too many pages (header/footer artifacts)
        tc = total_page_count(clean_refs)
        # Absolute ceiling: >200 pages = definitely header/footer noise (e.g., "october")
        if tc > 200:
            removed_high_count += 1
            garbage_log.append(f"  [header_artifact_{tc}pages] {term}")
            continue
        if tc > MAX_USEFUL_PAGES and clean_alpha not in TECHNICAL_TERMS_LOWER:
            if not is_real_word(term, spell_checker):
                removed_high_count += 1
                garbage_log.append(f"  [high_count_non_word] {term}")
                continue

        filtered[term] = clean_refs

    return filtered, removed_stops, removed_garbage, removed_high_count, removed_garbled, garbage_log


# --- Step 6: Format output ---
def format_refs(refs):
    parts = []
    for book in sorted(refs.keys()):
        pages = refs[book]
        page_str = " ".join(str(p) for p in pages)
        parts.append(f"(B{book}) {page_str}")
    return ", ".join(parts)


def build_output(entries, code_entries):
    lines = []
    lines.append("=" * 80)
    lines.append("SEC549 CLEAN INDEX -- Prepared by Cyrus (v3 - Dictionary Enhanced)")
    lines.append("GIAC Exam Reference -- Alphabetical Lookup")
    lines.append("Format: term > (Book#) page numbers")
    lines.append("=" * 80)
    lines.append("")

    # Separate alpha vs non-alpha
    alpha_entries = {t: r for t, r in entries.items() if t and t[0].isalpha()}
    other_entries = {t: r for t, r in entries.items() if t and not t[0].isalpha()}

    if other_entries:
        lines.append("\n-- # " + "-" * 74)
        for term in sorted(other_entries.keys()):
            ref_str = format_refs(other_entries[term])
            lines.append(f"  {term} > {ref_str}")

    current_letter = ""
    for term in sorted(alpha_entries.keys(), key=str.lower):
        first_char = term[0].upper()
        if first_char != current_letter:
            current_letter = first_char
            lines.append(f"\n-- {current_letter} " + "-" * 74)
        ref_str = format_refs(alpha_entries[term])
        lines.append(f"  {term} > {ref_str}")

    if code_entries:
        lines.append(f"\n\n{'=' * 80}")
        lines.append("CODE & PATH REFERENCES")
        lines.append("=" * 80)
        lines.append("")
        for term in sorted(code_entries.keys()):
            ref_str = format_refs(code_entries[term])
            lines.append(f"  {term} > {ref_str}")

    return "\n".join(lines)


# --- Main ---
def main():
    print("=" * 60)
    print("CYRUS -- Phase A v3: Enhanced Index Cleanup Pipeline")
    print("(Dictionary-validated, junk-suffix-stripped)")
    print("=" * 60)

    # Init spell checker
    print("\n[0/6] Initializing dictionary spell checker...")
    spell = init_spell_checker()
    print(f"  Loaded symspellpy + {len(TECHNICAL_TERMS_LOWER)} technical terms")

    # Parse
    print("\n[1/6] Parsing raw omega index...")
    raw = parse_omega_index(INPUT_FILE)
    print(f"  Parsed {len(raw)} raw entries")

    # Junk suffix stripping pre-pass
    print("\n[2/6] Stripping known junk suffixes...")
    stripped_count = 0
    cleaned_entries = {}
    for term, refs in raw.items():
        clean_term, was_stripped = strip_junk_suffix(term)
        if was_stripped:
            stripped_count += 1
            # If the cleaned term already exists, merge refs
            if clean_term in cleaned_entries:
                cleaned_entries[clean_term] = merge_refs(cleaned_entries[clean_term], refs)
            else:
                cleaned_entries[clean_term] = refs
        else:
            if term in cleaned_entries:
                cleaned_entries[term] = merge_refs(cleaned_entries[term], refs)
            else:
                cleaned_entries[term] = refs
    print(f"  Stripped junk suffixes from {stripped_count} entries")
    print(f"  Entries after suffix cleanup: {len(cleaned_entries)}")

    # Handle underscore-prefixed entries
    print("\n[3/6] Handling underscore-prefixed entries...")
    underscore_fixed = 0
    final_entries = {}
    for term, refs in cleaned_entries.items():
        if term.startswith('_') and len(term) > 1:
            clean = term[1:]
            underscore_fixed += 1
            if clean in final_entries:
                final_entries[clean] = merge_refs(final_entries[clean], refs)
            else:
                final_entries[clean] = refs
        else:
            if term in final_entries:
                final_entries[term] = merge_refs(final_entries[term], refs)
            else:
                final_entries[term] = refs
    print(f"  Fixed {underscore_fixed} underscore-prefixed entries")

    # Separate code/path refs
    print("\n[4/6] Separating code/path references...")
    word_entries = {}
    code_entries = {}
    page_zero_removed = 0

    for term, refs in final_entries.items():
        if is_page_zero_only(refs):
            page_zero_removed += 1
            continue
        if is_code_or_path(term):
            code_entries[term] = refs
        else:
            word_entries[term] = refs

    print(f"  Word-based entries: {len(word_entries)}")
    print(f"  Code/path refs:    {len(code_entries)}")
    print(f"  Page-0-only removed: {page_zero_removed}")

    # Cluster & merge (now without same-first-letter constraint)
    print("\n[5/6] Clustering & fuzzy-merging (enhanced, cross-letter)...")
    print(f"  (threshold: {FUZZY_THRESHOLD}% similarity)")
    merged = cluster_and_merge(word_entries, spell, FUZZY_THRESHOLD)
    absorbed = len(word_entries) - len(merged)
    print(f"  Absorbed {absorbed} duplicate/variant entries")
    print(f"  Remaining: {len(merged)}")

    # Final filter (dictionary-enhanced)
    print("\n[6/6] Final filtering (dictionary-validated)...")
    filtered, stops, garbage, high_count, garbled, garbage_log = final_filter(merged, spell)
    print(f"  Stop words removed:      {stops}")
    print(f"  Garbled entries removed:  {garbled}")
    print(f"  High page-count removed: {high_count}")
    print(f"  Low-quality removed:     {garbage}")
    print(f"  Final clean terms:       {len(filtered)}")

    # Output
    print("\n[7/6] Building clean index...")
    clean_code = {}
    for term, refs in code_entries.items():
        clean_refs = {b: [p for p in pages if p > 0] for b, pages in refs.items()}
        clean_refs = {b: p for b, p in clean_refs.items() if p}
        if clean_refs:
            clean_code[term] = clean_refs

    index_text = build_output(filtered, clean_code)
    output_path = OUTPUT_DIR / "SEC549_Clean_Index.txt"
    output_path.write_text(index_text, encoding="utf-8")
    print(f"  Saved: {output_path}")

    # Save garbage log
    garbage_path = DATA_DIR / "SEC549_Garbage_Entries.txt"
    garbage_path.write_text(
        "OCR GARBAGE ENTRIES (removed by v3 pipeline)\n" + "=" * 40 + "\n" + "\n".join(garbage_log),
        encoding="utf-8"
    )
    print(f"  Garbage log: {garbage_path}")

    total_final = len(filtered) + len(clean_code)
    total_raw = len(raw)
    removed = total_raw - total_final
    pct = (removed / total_raw) * 100 if total_raw else 0

    stats = {
        "pipeline_version": "v3-dictionary-enhanced",
        "raw_entries": total_raw,
        "junk_suffixes_stripped": stripped_count,
        "underscore_prefixes_fixed": underscore_fixed,
        "final_clean_terms": len(filtered),
        "code_path_refs": len(clean_code),
        "total_final": total_final,
        "removed_total": removed,
        "removed_pct": round(pct, 1),
        "page_zero_only": page_zero_removed,
        "fuzzy_merged": absorbed,
        "stop_words_removed": stops,
        "garbled_removed": garbled,
        "high_page_count_removed": high_count,
        "low_quality_removed": garbage,
    }
    stats_path = DATA_DIR / "SEC549_Index_Stats.json"
    stats_path.write_text(json.dumps(stats, indent=2), encoding="utf-8")

    print(f"\n{'=' * 60}")
    print(f"SUMMARY")
    print(f"  Raw:   {total_raw}")
    print(f"  Final: {total_final} ({len(filtered)} terms + {len(clean_code)} code/paths)")
    print(f"  Removed: {removed} ({pct:.1f}%)")
    print(f"{'=' * 60}")


if __name__ == "__main__":
    main()
