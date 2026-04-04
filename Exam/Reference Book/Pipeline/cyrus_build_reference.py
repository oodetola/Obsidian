"""
Cyrus -- Phase C: Build Reference Architecture
Assembles the SEC549 exam reference book content:
- Front matter (TOC, how-to-use, exam domain mapping)
- Topical quick-reference sections
- Cross-cloud comparison matrices
- CLI cheat sheet
- Acronym glossary
- Clean index
"""

import json
from pathlib import Path
from datetime import datetime

EXAM_DIR = Path(r"C:/Users/matth/Downloads/SEC549/Exam")
REF_DIR = EXAM_DIR / "Reference Book"
DATA_DIR = REF_DIR / "Data"


def load_json(filename):
    with open(DATA_DIR / filename, encoding="utf-8") as f:
        return json.load(f)


def load_text(filename):
    return (REF_DIR / filename).read_text(encoding="utf-8")


def build_reference_book():
    """Build the complete reference book as a single markdown document."""

    # Load extracted data
    cloud_services = load_json("SEC549_Cloud_Services.json")
    topic_map = load_json("SEC549_Topic_Map.json")
    cli_commands = load_json("SEC549_CLI_Commands.json")
    clean_index = load_text("SEC549_Clean_Index.txt")

    sections = []

    # =========================================================================
    # FRONT MATTER
    # =========================================================================
    sections.append("""
================================================================================
       SEC549 GIAC EXAM REFERENCE BOOK
       Cloud Security Architecture and Operations
       Prepared by Cyrus -- GIAC Exam Reference Architect
       Generated: {date}
================================================================================

HOW TO USE THIS REFERENCE
--------------------------
This book is a LOOKUP TOOL, not a study guide. Use it during the exam to find
answers in under 20 seconds.

NAVIGATION:
  1. Check the TOPIC SECTIONS (pp. 2-30) for concept questions
  2. Check the COMPARISON MATRICES (pp. 31-45) for cross-cloud questions
  3. Check the CLI CHEAT SHEET (pp. 46-55) for command syntax questions
  4. Check the ACRONYM GLOSSARY (pp. 56-60) for terminology questions
  5. Check the CLEAN INDEX (pp. 61+) for everything else -- look up the term
     and find the exact book/page in your SANS materials

EXAM FORMAT REMINDER:
  * 100-115 multiple choice questions
  * 2-3 hour time limit (~1-1.5 min per question)
  * Open book: this reference + your tabbed/annotated SANS books
  * Pace yourself: flag hard questions and come back

COLOR CODING (if printed in color):
  [AWS]   = Orange sections
  [AZURE] = Blue sections
  [GCP]   = Green sections

BOOK PAGE REFERENCE FORMAT:
  (B1) 42 = Book 1, page 42
  (B3) 95 = Book 3, page 95
""".format(date=datetime.now().strftime("%Y-%m-%d")))

    # =========================================================================
    # EXAM DOMAIN TO BOOK MAPPING
    # =========================================================================
    sections.append("""
================================================================================
  SECTION 0: EXAM DOMAIN TO BOOK MAPPING
================================================================================

  Book 1 (144 pages): Identity & Access Management Foundations
    - Cloud IAM concepts, identity models, access control (RBAC, ABAC, PBAC)
    - AWS IAM Identity Center (IdC/SSO), Organizations, SCPs
    - Azure Entra ID, Conditional Access, PIM
    - GCP Cloud IAM, Organization Policy
    - Identity federation (SAML, OIDC, OAuth)
    - Single sign-on, MFA, least privilege
    - Cross-account access, assume role

  Book 2 (137 pages): Authentication, Federation & Identity Attacks
    - Deep dive: SAML, OIDC, OAuth 2.0 flows
    - AWS Cognito, STS, credential management
    - Azure AD B2B/B2C, Managed Identity
    - GCP Workload Identity, service accounts
    - Credential theft, privilege escalation
    - Zero trust architecture foundations
    - Workload identity federation across clouds

  Book 3 (151 pages): Network Security & Segmentation
    - VPC/VNET architecture and design
    - Security groups, NACLs, NSGs, firewall rules
    - Network segmentation and microsegmentation
    - Private Link, Service Endpoints, VPC Service Controls
    - Transit Gateway, VPC Peering, hub-spoke models
    - DNS security, DDoS protection
    - Cloud interconnects (Direct Connect, ExpressRoute, Cloud VPN)

  Book 4 (158 pages): Cloud Security Governance & Data Protection
    - Data classification and encryption (at rest, in transit)
    - Key management (KMS, Key Vault, Cloud KMS)
    - Secret management (Secrets Manager, Key Vault, Secret Manager)
    - Compliance frameworks and governance
    - Cloud security posture management
    - Container security (EKS, AKS, GKE)
    - Logging, monitoring, and audit trails

  Book 5 (103 pages): Detection, Response & Security Operations
    - SIEM and security operations
    - CloudTrail, Azure Monitor, Cloud Audit Logs
    - GuardDuty, Defender for Cloud, Security Command Center
    - Incident response in cloud environments
    - Threat detection and investigation
    - Security automation and DevSecOps
    - Flow logs, VPC flow analysis
""")

    # =========================================================================
    # SECTION 1: IDENTITY & ACCESS MANAGEMENT
    # =========================================================================
    sections.append("""
================================================================================
  SECTION 1: IDENTITY & ACCESS MANAGEMENT
================================================================================

--- 1.1 IAM SERVICE COMPARISON ---

  Feature              | AWS                    | Azure                  | GCP
  ---------------------|------------------------|------------------------|------------------------
  IAM Service          | AWS IAM                | Entra ID (Azure AD)    | Cloud IAM
  Identity Center      | IAM Identity Center    | Entra ID               | Cloud Identity
  SSO                  | IAM IdC SSO            | Entra ID SSO           | Cloud Identity SSO
  Root/Global Admin    | Root Account           | Global Administrator   | Super Admin
  Service Account      | IAM Role (for service) | Managed Identity       | Service Account
  Temporary Creds      | STS AssumeRole         | Managed Identity Token | Service Account Key
  MFA                  | IAM MFA / IdC MFA      | Entra MFA              | 2-Step Verification
  Conditional Access   | IAM Conditions         | Conditional Access     | Access Context Manager
  Privileged Access    | N/A (use SCPs)         | PIM                    | PAM (preview)
  External Identity    | Cognito / SAML/OIDC    | B2B / B2C              | Workload Identity Fed.
  Access Review        | Access Analyzer        | Access Reviews         | IAM Recommender

--- 1.2 ACCESS CONTROL MODELS ---

  Model    | Description                        | Where Used
  ---------|------------------------------------|--------------------------------------------
  RBAC     | Role-Based Access Control           | Azure (primary), AWS (IAM roles), GCP
  ABAC     | Attribute-Based Access Control      | AWS (tags), Azure (conditions), GCP (conditions)
  PBAC     | Policy-Based Access Control         | AWS IAM policies, GCP IAM bindings
  ACL      | Access Control Lists                | AWS S3, network ACLs
  ReBAC    | Relationship-Based Access Control   | Google Zanzibar (internal)

--- 1.3 AWS IAM HIERARCHY ---

  Organization (Management Account)
    |-- Organizational Units (OUs)
    |     |-- Accounts
    |           |-- IAM Users / Roles / Groups
    |           |-- Policies (Identity, Resource, SCPs, Permission Boundaries)
    |
    |-- Service Control Policies (SCPs) -- guardrails at OU/account level
    |-- Tag Policies, Backup Policies, AI Services Opt-out

  KEY DISTINCTION: SCPs are DENY guardrails (they restrict, not grant).
  Permission Boundary = max permissions an IAM entity CAN have.
  Identity Policy = what the entity IS allowed to do.
  Effective permissions = Identity Policy INTERSECT Permission Boundary INTERSECT SCP

--- 1.4 AZURE ENTRA ID HIERARCHY ---

  Tenant (Entra ID Directory)
    |-- Management Groups
    |     |-- Subscriptions
    |           |-- Resource Groups
    |                 |-- Resources
    |
    |-- Users / Groups / Service Principals / Managed Identities
    |-- Enterprise Applications (SSO targets)
    |-- Conditional Access Policies
    |-- PIM (Privileged Identity Management) -- just-in-time access

  KEY DISTINCTION: Azure RBAC is inherited down the hierarchy.
  Deny assignments override allow (explicit deny wins).
  Conditional Access = context-aware access gating (location, device, risk).

--- 1.5 GCP IAM HIERARCHY ---

  Organization
    |-- Folders
    |     |-- Projects
    |           |-- Resources
    |
    |-- IAM Policy Bindings (member + role + condition)
    |-- Organization Policies (constraints at org/folder/project level)

  KEY DISTINCTION: GCP IAM is additive (allow-only, no explicit deny except Org Policy).
  Deny policies now exist (preview/GA) but are separate from IAM allow policies.
  Organization Policy = constraints (like SCPs) applied at org/folder/project level.
""")

    # =========================================================================
    # SECTION 2: AUTHENTICATION & FEDERATION
    # =========================================================================
    sections.append("""
================================================================================
  SECTION 2: AUTHENTICATION & FEDERATION
================================================================================

--- 2.1 IDENTITY FEDERATION PROTOCOLS ---

  Protocol | Purpose                | Token Type   | Key Flow
  ---------|------------------------|--------------|----------------------------------
  SAML 2.0 | Enterprise SSO         | XML Assertion| Browser redirect, POST binding
  OIDC     | Modern auth (OpenID)   | JWT ID Token | Authorization Code + PKCE
  OAuth2.0 | Authorization (not authn)| Access Token| Auth Code, Client Credentials
  Kerberos | On-prem AD auth        | TGT/TGS      | KDC ticket exchange
  LDAP     | Directory queries      | N/A          | Bind + search

  CRITICAL DISTINCTION:
  - SAML = authentication (who are you?) -- enterprise SSO
  - OAuth = authorization (what can you access?) -- API access
  - OIDC = authentication ON TOP of OAuth -- modern apps

--- 2.2 FEDERATION ACROSS CLOUDS ---

  Scenario                      | AWS                          | Azure                     | GCP
  ------------------------------|------------------------------|---------------------------|-----------------------------
  Federate with on-prem AD      | SAML to IAM/IdC              | Entra Connect Sync        | Cloud Identity + SAML
  Federate between clouds       | OIDC/STS AssumeRole          | Workload Identity Fed.    | Workload Identity Federation
  Workload-to-cloud (CI/CD)     | OIDC Provider + AssumeRole   | Federated Credentials     | Workload Identity Provider
  External users (B2C)          | Cognito User Pools           | Azure AD B2C              | Identity Platform
  M2M (machine-to-machine)      | IAM Role + STS               | Managed Identity          | Service Account

--- 2.3 AWS STS (Security Token Service) ---

  API Call                        | Use Case
  --------------------------------|------------------------------------------------
  AssumeRole                      | Cross-account access, temporary elevated privs
  AssumeRoleWithSAML              | SAML-based federation from IdP
  AssumeRoleWithWebIdentity       | OIDC federation (Cognito, GitHub, etc.)
  GetFederationToken              | Temporary creds for federated users
  GetSessionToken                 | MFA-authenticated temporary creds
  GetCallerIdentity               | "Who am I?" -- verify current identity

--- 2.4 AZURE MANAGED IDENTITY ---

  Type                | Description                         | Use Case
  --------------------|-------------------------------------|------------------------------
  System-Assigned     | Tied to resource lifecycle          | Single resource auth
  User-Assigned       | Independent lifecycle               | Shared across resources

  KEY: Managed Identity eliminates credential management.
  No secrets to rotate. Token automatically provisioned via IMDS (169.254.169.254).

--- 2.5 GCP SERVICE ACCOUNTS ---

  Type                    | Description
  ------------------------|---------------------------------------------
  Default                 | Auto-created, overly permissive -- AVOID
  User-Managed            | Created by admin, custom permissions
  Google-Managed          | Used by Google services internally

  KEY: Service account keys are long-lived credentials -- prefer Workload Identity.
  Workload Identity Federation = keyless auth from external IdPs to GCP.
""")

    # =========================================================================
    # SECTION 3: NETWORK SECURITY
    # =========================================================================
    sections.append("""
================================================================================
  SECTION 3: NETWORK SECURITY & SEGMENTATION
================================================================================

--- 3.1 NETWORK SECURITY CONTROLS COMPARISON ---

  Control              | AWS                    | Azure                  | GCP
  ---------------------|------------------------|------------------------|------------------------
  Virtual Network      | VPC                    | VNet                   | VPC
  Subnet               | Subnet                 | Subnet                 | Subnet (regional)
  Stateful Firewall    | Security Group (SG)    | NSG                    | Firewall Rules
  Stateless Firewall   | Network ACL (NACL)     | N/A                    | N/A
  Web App Firewall     | AWS WAF                | Azure WAF              | Cloud Armor
  DDoS Protection      | Shield (Std/Adv)       | DDoS Protection        | Cloud Armor
  Network Firewall     | AWS Network Firewall   | Azure Firewall         | Cloud NGFW
  DNS Firewall         | Route 53 Resolver DNS  | Azure DNS Private      | Cloud DNS
  Flow Logs            | VPC Flow Logs          | NSG Flow Logs          | VPC Flow Logs

--- 3.2 NETWORK SEGMENTATION PATTERNS ---

  Pattern              | Description                              | Where Covered
  ---------------------|------------------------------------------|---------------
  VPC/VNet Isolation   | Separate workloads in different VPCs     | B3
  Subnet Tiers         | Public/private/data subnet layers        | B3
  Security Groups      | Instance-level micro-segmentation        | B3
  Hub-Spoke            | Central hub VPC with spoke VPC peers     | B3
  Transit Gateway      | Centralized routing between VPCs         | B3
  Service Mesh         | App-layer segmentation (Istio, Linkerd)  | B3
  Zero Trust Network   | Never trust, always verify               | B2, B3

--- 3.3 PRIVATE CONNECTIVITY ---

  Feature              | AWS                    | Azure                  | GCP
  ---------------------|------------------------|------------------------|------------------------
  Private Endpoint     | PrivateLink (Interface)| Private Endpoint       | Private Service Connect
  Service Endpoint     | Gateway Endpoint (S3,DDB)| Service Endpoint     | Private Google Access
  Private DNS          | Route 53 Private Zones | Private DNS Zone       | Cloud DNS Private Zone
  Hybrid Connect       | Direct Connect         | ExpressRoute           | Cloud Interconnect
  VPN                  | Site-to-Site VPN       | VPN Gateway            | Cloud VPN
  Peering              | VPC Peering            | VNet Peering           | VPC Peering
  Transit              | Transit Gateway        | Virtual WAN            | N/A (use peering)

--- 3.4 KEY SECURITY GROUP / NSG CONCEPTS ---

  AWS Security Groups:
  - STATEFUL (return traffic auto-allowed)
  - Default: deny all inbound, allow all outbound
  - Rules are ALLOW only (no deny rules)
  - Applied at ENI (instance) level

  AWS NACLs:
  - STATELESS (must allow both directions)
  - Default: allow all inbound and outbound
  - Rules have ALLOW and DENY, processed in order
  - Applied at subnet level

  Azure NSGs:
  - STATEFUL
  - Default rules: allow VNet-to-VNet, allow LB, deny all inbound from internet
  - Priority-based (lower number = higher priority)
  - Applied at subnet or NIC level

  GCP Firewall Rules:
  - STATEFUL
  - Default: deny all ingress, allow all egress
  - Priority-based (lower number = higher priority)
  - Applied via network tags or service accounts
""")

    # =========================================================================
    # SECTION 4: DATA PROTECTION & ENCRYPTION
    # =========================================================================
    sections.append("""
================================================================================
  SECTION 4: DATA PROTECTION & ENCRYPTION
================================================================================

--- 4.1 ENCRYPTION COMPARISON ---

  Feature              | AWS                    | Azure                  | GCP
  ---------------------|------------------------|------------------------|------------------------
  KMS                  | AWS KMS                | Azure Key Vault        | Cloud KMS
  HSM                  | CloudHSM               | Managed HSM            | Cloud HSM
  Default Encryption   | SSE-S3, SSE-KMS        | Azure Storage SSE      | Google-managed key
  Customer-Managed Key | CMK in KMS             | CMK in Key Vault       | CMEK in Cloud KMS
  Customer-Supplied Key| SSE-C                  | N/A (use CMK)          | CSEK
  Key Rotation         | Auto (1 year) or manual| Auto or manual         | Auto (1 year) or manual
  Envelope Encryption  | Data Key + Master Key  | DEK + KEK              | DEK + KEK
  Secret Management    | Secrets Manager        | Key Vault Secrets      | Secret Manager
  Certificate Mgmt     | ACM                    | Key Vault Certificates | Certificate Authority

--- 4.2 ENCRYPTION AT REST vs IN TRANSIT ---

  At Rest:
  - Data stored on disk (S3, EBS, Azure Storage, GCS, databases)
  - Use KMS/Key Vault/Cloud KMS for key management
  - Envelope encryption: encrypt data with DEK, encrypt DEK with KEK
  - Key hierarchy: Root Key > Key Encryption Key > Data Encryption Key

  In Transit:
  - Data moving over network (API calls, web traffic, replication)
  - TLS 1.2+ for all cloud API endpoints (enforced by default)
  - mTLS for service-to-service in service mesh
  - VPN/private connectivity for hybrid connections

--- 4.3 KEY MANAGEMENT HIERARCHY ---

  Level          | AWS                | Azure              | GCP
  ---------------|--------------------|--------------------|--------------------
  Root of Trust  | AWS-managed root   | Platform-managed   | Google root key
  Master Key     | KMS CMK            | Key Vault Key      | Cloud KMS Key
  Data Key       | Generated by KMS   | Generated by KV    | Generated by KMS
  Envelope       | Encrypt DEK w/ CMK | Encrypt DEK w/ KEK | Encrypt DEK w/ KEK
""")

    # =========================================================================
    # SECTION 5: LOGGING, MONITORING & DETECTION
    # =========================================================================
    sections.append("""
================================================================================
  SECTION 5: LOGGING, MONITORING & DETECTION
================================================================================

--- 5.1 LOGGING SERVICES COMPARISON ---

  Feature              | AWS                    | Azure                  | GCP
  ---------------------|------------------------|------------------------|------------------------
  API/Control Plane    | CloudTrail             | Activity Log           | Cloud Audit Logs
  Data Plane           | CloudTrail Data Events | Diagnostic Settings    | Data Access Logs
  Network              | VPC Flow Logs          | NSG Flow Logs          | VPC Flow Logs
  DNS                  | Route 53 Query Logs    | DNS Analytics          | Cloud DNS Logs
  Compute              | CloudWatch Logs        | Log Analytics          | Cloud Logging
  SIEM                 | SecurityHub            | Sentinel               | Security Command Center
  Threat Detection     | GuardDuty              | Defender for Cloud     | Security Command Center
  Config Compliance    | AWS Config             | Azure Policy           | Security Health Analytics
  Vulnerability Scan   | Inspector              | Defender (servers)     | Web Security Scanner

--- 5.2 CRITICAL LOGS TO ENABLE ---

  AWS:
  - CloudTrail: ALL regions, management + data events
  - S3 access logging for sensitive buckets
  - VPC Flow Logs on all VPCs
  - GuardDuty in all regions
  - Config rules for compliance

  Azure:
  - Activity Log: forwarded to Log Analytics workspace
  - Diagnostic Settings on all critical resources
  - NSG Flow Logs (v2 with traffic analytics)
  - Defender for Cloud on all subscriptions
  - Sentinel for SIEM and SOAR

  GCP:
  - Cloud Audit Logs: Admin Activity (always on), Data Access (enable)
  - VPC Flow Logs on all subnets
  - Cloud Logging export to BigQuery for analysis
  - Security Command Center Premium
  - Organization-level logging sink

--- 5.3 INCIDENT RESPONSE IN CLOUD ---

  Phase          | Key Actions
  ---------------|---------------------------------------------------------
  Preparation    | Enable logging, set up alerts, define playbooks
  Detection      | GuardDuty/Defender/SCC findings, SIEM alerts
  Containment    | Isolate (SG/NSG changes), revoke credentials, snapshot
  Eradication    | Remove malware, patch vulns, rotate keys
  Recovery       | Restore from clean backup, validate, re-enable
  Lessons Learned| Update playbooks, improve detection, share findings
""")

    # =========================================================================
    # SECTION 6: ZERO TRUST & GOVERNANCE
    # =========================================================================
    sections.append("""
================================================================================
  SECTION 6: ZERO TRUST ARCHITECTURE & GOVERNANCE
================================================================================

--- 6.1 ZERO TRUST PRINCIPLES ---

  1. Never trust, always verify
  2. Assume breach
  3. Verify explicitly (identity, device, location, behavior)
  4. Least privilege access
  5. Microsegmentation
  6. Continuous validation

  CISA Zero Trust Maturity Model Pillars:
  - Identity
  - Devices
  - Networks
  - Applications & Workloads
  - Data

--- 6.2 SHARED RESPONSIBILITY MODEL ---

  Layer              | IaaS          | PaaS          | SaaS
  -------------------|---------------|---------------|---------------
  Data               | Customer      | Customer      | Customer
  Applications       | Customer      | Customer      | Provider
  Runtime            | Customer      | Provider      | Provider
  OS                 | Customer      | Provider      | Provider
  Virtualization     | Provider      | Provider      | Provider
  Network            | Provider      | Provider      | Provider
  Physical           | Provider      | Provider      | Provider

  KEY: Customer ALWAYS responsible for data classification and access control.

--- 6.3 GOVERNANCE COMPARISON ---

  Feature              | AWS                    | Azure                  | GCP
  ---------------------|------------------------|------------------------|------------------------
  Policy Guardrails    | SCPs (Org)             | Azure Policy           | Organization Policy
  Compliance           | AWS Config Rules       | Azure Policy (built-in)| Security Health Analytics
  Landing Zone         | Control Tower          | Azure Landing Zones    | Cloud Foundation Toolkit
  Resource Tagging     | Tag Policies           | Azure Policy (tags)    | Labels
  Cost Management      | Cost Explorer          | Cost Management        | Billing Reports
  Blueprints           | Service Catalog        | Blueprints             | Deployment Manager
""")

    # =========================================================================
    # SECTION 7: CONTAINER & KUBERNETES SECURITY
    # =========================================================================
    sections.append("""
================================================================================
  SECTION 7: CONTAINER & KUBERNETES SECURITY
================================================================================

--- 7.1 MANAGED KUBERNETES COMPARISON ---

  Feature              | AWS EKS              | Azure AKS              | GCP GKE
  ---------------------|----------------------|------------------------|------------------------
  Control Plane        | AWS-managed          | Azure-managed          | Google-managed
  Node Auth            | IAM Roles for SA     | Managed Identity       | Workload Identity
  Network Policy       | Calico               | Azure NPM / Calico    | Calico / Dataplane V2
  Pod Security         | Pod Security Standards| Pod Security Standards | Pod Security Standards
  Image Scanning       | ECR Scanning         | Defender for Containers| Artifact Analysis
  Registry             | ECR                  | ACR                    | Artifact Registry
  Secrets              | Secrets Manager CSI  | Key Vault CSI          | Secret Manager CSI
  Service Mesh         | App Mesh             | Istio add-on           | Anthos Service Mesh
  Binary Auth          | N/A (use Kyverno)    | N/A (use Gatekeeper)   | Binary Authorization

--- 7.2 CONTAINER SECURITY CHECKLIST ---

  [ ] Use minimal base images (distroless, Alpine)
  [ ] Scan images for vulnerabilities in CI/CD
  [ ] Sign and verify images (cosign, Notation)
  [ ] Run containers as non-root
  [ ] Use read-only root filesystem
  [ ] Apply Pod Security Standards (Restricted)
  [ ] Use Network Policies to restrict pod-to-pod traffic
  [ ] Use Workload Identity (not node-level credentials)
  [ ] Encrypt secrets at rest in etcd
  [ ] Enable audit logging for Kubernetes API
""")

    # =========================================================================
    # CLI CHEAT SHEET
    # =========================================================================
    sections.append("""
================================================================================
  CLI CHEAT SHEET -- COMMON SECURITY COMMANDS
================================================================================

--- AWS CLI ---

  # Identity & access
  aws sts get-caller-identity                          # Who am I?
  aws sts assume-role --role-arn <ARN> --role-session-name <name>
  aws iam list-users                                   # List IAM users
  aws iam list-roles                                   # List IAM roles
  aws iam list-attached-user-policies --user-name <u>  # User's policies
  aws iam get-policy-version --policy-arn <ARN> --version-id v1
  aws iam list-access-keys --user-name <u>             # Check for keys
  aws organizations list-accounts                       # Org accounts
  aws organizations describe-organization               # Org details

  # Logging & detection
  aws cloudtrail describe-trails                        # List trails
  aws guardduty list-detectors                          # GuardDuty status
  aws securityhub describe-hub                          # SecurityHub status
  aws config describe-config-rules                      # Config rules
  aws logs describe-log-groups                          # CloudWatch logs

  # Network & encryption
  aws ec2 describe-vpcs                                 # List VPCs
  aws ec2 describe-security-groups                      # List SGs
  aws ec2 describe-flow-logs                            # Flow logs
  aws kms list-keys                                     # KMS keys
  aws s3api get-bucket-encryption --bucket <name>       # S3 encryption

--- Azure CLI ---

  # Identity & access
  az account show                                       # Current context
  az ad user list                                       # List AD users
  az ad sp list --all                                   # Service principals
  az role assignment list --all                         # RBAC assignments
  az role definition list --custom-role-only true       # Custom roles
  az ad app list --all                                  # App registrations
  az identity list                                      # Managed identities

  # Logging & detection
  az monitor activity-log list                          # Activity log
  az security assessment list                           # Defender findings
  az sentinel alert-rule list --workspace-name <ws>     # Sentinel rules

  # Network & encryption
  az network vnet list                                  # List VNets
  az network nsg list                                   # List NSGs
  az keyvault list                                      # Key Vaults
  az storage account list                               # Storage accounts

--- gcloud CLI ---

  # Identity & access
  gcloud auth list                                      # Active accounts
  gcloud projects get-iam-policy <PROJECT>              # IAM bindings
  gcloud iam roles list --project <PROJECT>             # Custom roles
  gcloud iam service-accounts list                      # Service accounts
  gcloud organizations list                             # Organizations
  gcloud resource-manager org-policies list --organization <ORG>

  # Logging & detection
  gcloud logging logs list                              # Available logs
  gcloud logging read "logName=projects/<P>/logs/cloudaudit.googleapis.com"
  gcloud scc findings list --organization <ORG>         # SCC findings

  # Network & encryption
  gcloud compute networks list                          # VPCs
  gcloud compute firewall-rules list                    # Firewall rules
  gcloud kms keys list --location <LOC> --keyring <KR>  # KMS keys

--- kubectl ---

  kubectl auth can-i --list                             # My permissions
  kubectl get pods --all-namespaces                     # All pods
  kubectl get networkpolicies --all-namespaces          # Network policies
  kubectl get clusterroles                              # RBAC cluster roles
  kubectl get secrets --all-namespaces                  # Secrets (names)
""")

    # =========================================================================
    # ACRONYM GLOSSARY
    # =========================================================================
    sections.append("""
================================================================================
  ACRONYM GLOSSARY
================================================================================

  ABAC    Attribute-Based Access Control
  ACL     Access Control List
  ACM     AWS Certificate Manager
  AD      Active Directory (Azure/on-prem)
  AKS     Azure Kubernetes Service
  ALB     Application Load Balancer
  API     Application Programming Interface
  ARN     Amazon Resource Name
  ASG     Auto Scaling Group
  ATP     Advanced Threat Protection

  B2B     Business-to-Business (Azure AD)
  B2C     Business-to-Consumer (Azure AD)
  BCP     Business Continuity Plan
  BGP     Border Gateway Protocol

  CASB    Cloud Access Security Broker
  CDN     Content Delivery Network
  CIEM    Cloud Infrastructure Entitlement Management
  CIDR    Classless Inter-Domain Routing
  CMEK    Customer-Managed Encryption Key
  CMK     Customer Master Key (AWS KMS)
  CNAPP   Cloud-Native Application Protection Platform
  CORS    Cross-Origin Resource Sharing
  CSA     Cloud Security Alliance
  CSEK    Customer-Supplied Encryption Key
  CSPM    Cloud Security Posture Management
  CWPP    Cloud Workload Protection Platform
  CVE     Common Vulnerabilities and Exposures

  DAC     Discretionary Access Control
  DEK     Data Encryption Key
  DDoS    Distributed Denial of Service
  DLP     Data Loss Prevention
  DMZ     Demilitarized Zone
  DNS     Domain Name System
  DRP     Disaster Recovery Plan

  EBS     Elastic Block Store
  EC2     Elastic Compute Cloud
  ECR     Elastic Container Registry
  ECS     Elastic Container Service
  EKS     Elastic Kubernetes Service
  ENI     Elastic Network Interface

  FIDO2   Fast Identity Online version 2
  FIM     File Integrity Monitoring

  GCS     Google Cloud Storage
  GKE     Google Kubernetes Engine

  HSM     Hardware Security Module
  HTTP    Hypertext Transfer Protocol
  HTTPS   HTTP Secure

  IaC     Infrastructure as Code
  IAM     Identity and Access Management
  IdC     Identity Center (AWS)
  IDP     Identity Provider
  IMDS    Instance Metadata Service (169.254.169.254)
  IOC     Indicator of Compromise

  JIT     Just-In-Time (access)
  JSON    JavaScript Object Notation
  JWT     JSON Web Token

  KDC     Key Distribution Center (Kerberos)
  KEK     Key Encryption Key
  KMS     Key Management Service

  LDAP    Lightweight Directory Access Protocol

  MAC     Mandatory Access Control
  MFA     Multi-Factor Authentication
  MITRE   MITRE ATT&CK Framework
  mTLS    Mutual Transport Layer Security

  NACL    Network Access Control List (AWS)
  NAT     Network Address Translation
  NLB     Network Load Balancer
  NSG     Network Security Group (Azure)

  OIDC    OpenID Connect
  OPA     Open Policy Agent
  OU      Organizational Unit

  PAM     Privileged Access Management
  PBAC    Policy-Based Access Control
  PII     Personally Identifiable Information
  PIM     Privileged Identity Management (Azure)
  PKI     Public Key Infrastructure
  PSP     Pod Security Policy (deprecated)
  PSS     Pod Security Standards

  RBAC    Role-Based Access Control

  S3      Simple Storage Service
  SAML    Security Assertion Markup Language
  SAS     Shared Access Signature (Azure)
  SCC     Security Command Center (GCP)
  SCP     Service Control Policy (AWS)
  SDK     Software Development Kit
  SG      Security Group (AWS)
  SIEM    Security Information and Event Management
  SLA     Service Level Agreement
  SNI     Server Name Indication
  SOAR    Security Orchestration, Automation & Response
  SOC     Security Operations Center
  SP      Service Principal (Azure)
  SPN     Service Principal Name
  SSE     Server-Side Encryption
  SSO     Single Sign-On
  STS     Security Token Service (AWS)

  TGS     Ticket Granting Service (Kerberos)
  TGT     Ticket Granting Ticket (Kerberos)
  TLS     Transport Layer Security

  VNet    Virtual Network (Azure)
  VPC     Virtual Private Cloud
  VPN     Virtual Private Network

  WAF     Web Application Firewall
  WORM    Write Once Read Many

  XDR     Extended Detection and Response
  XML     Extensible Markup Language

  ZTA     Zero Trust Architecture
  ZTNA    Zero Trust Network Access
""")

    # =========================================================================
    # CLEAN INDEX
    # =========================================================================
    sections.append("""
================================================================================
  ALPHABETICAL INDEX
  (Lookup any term -- find Book/Page in your SANS materials)
================================================================================
""")
    sections.append(clean_index)

    # Assemble final document
    full_doc = "\n".join(sections)
    return full_doc


def main():
    print("=" * 60)
    print("CYRUS -- Phase C: Building Reference Architecture")
    print("=" * 60)

    print("\n  Building reference book content...")
    doc = build_reference_book()

    output_path = REF_DIR / "SEC549_Exam_Reference_Book.md"
    output_path.write_text(doc, encoding="utf-8")
    print(f"  Saved: {output_path}")

    # Count sections and approximate pages
    lines = doc.count('\n')
    est_pages = lines // 55  # rough estimate: ~55 lines per printed page
    print(f"  Total lines: {lines}")
    print(f"  Estimated print pages: {est_pages}")

    print(f"\n{'=' * 60}")
    print("PHASE C COMPLETE")
    print(f"  Reference book assembled: {output_path.name}")
    print(f"  Sections: Front Matter, IAM, Auth/Federation, Network,")
    print(f"            Data Protection, Logging/Detection, Zero Trust,")
    print(f"            Containers, CLI Cheat Sheet, Acronyms, Index")
    print(f"{'=' * 60}")


if __name__ == "__main__":
    main()
