"""
Add missing compound terms to SEC549_Clean_Index.txt
Inserts terms alphabetically into the correct positions.
"""

from pathlib import Path

REF_DIR = Path(r"C:/Users/matth/Downloads/SEC549/Exam/Reference Book")
INDEX_FILE = REF_DIR / "SEC549_Clean_Index.txt"

# All missing compound terms to add
MISSING_TERMS = {
    # === Found in Book Topic Titles ===
    "access context manager": "(B2) 33 34 36 37 38 39",
    "access points (s3)": "(B4) 60",
    "activity log (azure)": "(B5) 29 30 31",
    "application service principals": "(B2) 93",
    "attack surface": "(B1) 106",
    "azure policy": "(B1) 108, (B4) 28",
    "certificate authority": "(B2) 108",
    "client-side encryption": "(B4) 95",
    "cloud audit logs": "(B4) 29 47, (B5) 29 47",
    "cloud-focused soc": "(B5) 4",
    "cloud identity": "(B1) 68 69 71 127 129",
    "cloud-managed encryption key": "(B4) 103 104 105",
    "cloud network connectivity center": "(B3) 73 74",
    "cloud storage": "(B4) 116",
    "conditional access": "(B2) 31 32 33 34 47 49 50 51 53 55 63",
    "confused deputy problem": "(B5) 53",
    "control-plane logs": "(B5) 26 27 29 30 31 33",
    "cribl": "(B5) 66",
    "cross-cloud": "(B2) 87, (B4) 151",
    "customer-managed encryption key": "(B4) 107 108 109 111 112 116",
    "data classification": "(B4) 22",
    "data exfiltration": "(B3) 56 127, (B4) 8 59",
    "data lake": "(B4) 90, (B5) 46 47",
    "data security framework": "(B4) 10 16 17",
    "defense in depth": "(B4) 7 8",
    "disaster recovery": "(B4) 147",
    "east-west traffic": "(B3) 95 96",
    "envelope encryption": "(B4) 100 102",
    "essential contacts": "(B5) 20",
    "event router": "(B5) 21 23 45",
    "firewall manager": "(B3) 49",
    "flow logs": "(B1) 70, (B3) 24 37, (B5) 36 37 38",
    "gateway endpoint": "(B4) 59",
    "guardrail resources": "(B1) 103 106 107",
    "hierarchical firewall policies": "(B3) 50",
    "hub attachments": "(B3) 74",
    "hybrid cloud network": "(B3) 81 82",
    "identity federation": "(B1) 44, (B2) 104 128 134",
    "identity perimeter": "(B5) 93",
    "inspection network": "(B3) 91 94 95 96 102 103 105 109",
    "key management options": "(B4) 97",
    "key rotation": "(B4) 109",
    "least privilege": "(B1) 22 41 113 121 128 131, (B2) 16 29 94, (B3) 33 41, (B4) 7 12, (B5) 90 93 98",
    "managed identities": "(B2) 94",
    "micro-segmentation": "(B3) 59",
    "microsoft sentinel": "(B5) 61 62 63 64 65 73 78 79 81 84 85 86 88",
    "nat gateway": "(B3) 11 16",
    "network access control list (nacl)": "(B3) 24",
    "network policy (kubernetes)": "(B3) 96",
    "network segmentation": "(B3) 56 57 59",
    "north-south traffic": "(B3) 89 90 91 92 93 94",
    "organizational units": "(B1) 92",
    "palo alto": "(B3) 119 122",
    "policy as code": "(B1) 51",
    "private endpoint": "(B3) 31 129 132 137 140",
    "private google access": "(B3) 130",
    "private hosted zones": "(B3) 144",
    "privatelink": "(B3) 132 137 140",
    "privileged access design": "(B1) 129 131 133 135 137",
    "pull architecture": "(B5) 67 68",
    "push architecture": "(B5) 66 67",
    "resource hierarchy": "(B1) 78 80 84 94 95",
    "role bindings": "(B1) 126",
    "route 53": "(B3) 144",
    "route table": "(B3) 18 22 23",
    "security advisory bulletins": "(B5) 12 14",
    "security command center": "(B4) 16, (B5) 42",
    "security data lake": "(B5) 46 47 58",
    "security group": "(B1) 82, (B3) 24 25 41 49 56 59, (B5) 36 92",
    "security hub": "(B5) 41 51",
    "security lake": "(B5) 47",
    "sensitive actions": "(B5) 42",
    "server-side encryption": "(B4) 94",
    "service control policy": "(B1) 103 106, (B3) 41 42",
    "service endpoint": "(B3) 129",
    "service principal": "(B2) 89 93, (B5) 53",
    "shared responsibility model": "(B5) 12",
    "shared services architecture": "(B3) 148",
    "single sign-on": "(B1) 46",
    "storage lifecycle": "(B4) 42",
    "tag policies": "(B4) 26 28",
    "threat model": "(B1) 39, (B2) 4 28, (B3) 4 34, (B4) 31, (B5) 4 19",
    "threat modeling": "(B1) 21, (B5) 100",
    "transit gateway": "(B3) 70 71 72 76 87 109, (B5) 92",
    "trust boundaries": "(B1) 26 29",
    "trust policy": "(B2) 127",
    "trust zones": "(B1) 29",
    "virtual wan (vwan)": "(B3) 70 71 72 76",
    "vpc peering": "(B3) 16 17 55 59 61 62 63 64 65 66 67 68 69 70",
    "vpc service controls": "(B3) 130, (B4) 59",
    "workload identity": "(B2) 130 131 132, (B4) 151",
    "workload identity federation": "(B2) 100 104 125 126 127 128 130 131 132 133 134",
    "workload identity pool": "(B2) 131 132",
    "zero trust": "(B2) 4 8 14 16 21 28 29, (B4) 9",
    "zero trust data security": "(B4) 9",

    # === Found in Cloud Services / Key Terms Metadata ===
    "access analyzer": "(B4) 16",
    "application gateway (azure)": "(B3) 105",
    "aws config": "(B1) 84, (B2) 88, (B3) 6, (B4) 16 41, (B5) 21",
    "aws shield": "(B3) 105",
    "azure front door": "(B3) 105",
    "binary authorization": "(B2) 105",
    "cloud armor": "(B3) 105",
    "cloud dns": "(B3) 144",
    "cloud functions": "(B4) 155, (B5) 84",
    "cloud hsm": "(B4) 97",
    "cloud interconnect": "(B3) 82",
    "cloud run": "(B2) 105, (B5) 31",
    "cloud vpn": "(B3) 82",
    "ddos protection": "(B3) 105, (B5) 92",
    "direct connect": "(B3) 82",
    "eventbridge": "(B5) 23 45 68",
    "expressroute": "(B3) 82",
    "log analytics": "(B4) 16, (B5) 45 51 62 64",
    "organization policy": "(B1) 107, (B2) 105, (B3) 50, (B4) 16",
    "secrets manager": "(B1) 137, (B4) 97",
    "shared vpc": "(B3) 38 41",
}


def main():
    # Read the existing index
    content = INDEX_FILE.read_text(encoding="utf-8")
    lines = content.split("\n")

    # Parse existing entries to find where to insert
    # Format: "  term > (B#) pages"
    # Letter headers: "-- A ----..."

    # Build list of (line_index, sort_key) for existing entries
    entries = []
    for i, line in enumerate(lines):
        stripped = line.strip()
        if stripped.startswith("--") and "---" in stripped:
            # Letter header
            continue
        if stripped and ">" in stripped:
            term = stripped.split(">")[0].strip().lower()
            entries.append((i, term))

    # Format new entries
    new_entries = []
    for term, pages in MISSING_TERMS.items():
        formatted = f"  {term} > {pages}"
        new_entries.append((term.lower(), formatted))

    # Sort new entries
    new_entries.sort(key=lambda x: x[0])

    # Insert new entries into the correct positions
    # Strategy: find the right letter section, then insert in sorted order
    new_lines = list(lines)
    offset = 0  # track insertions

    for sort_key, formatted_line in new_entries:
        # Find the correct insertion point
        first_char = sort_key[0] if sort_key[0].isalpha() else '#'

        # Find the letter section
        section_start = None
        section_end = None
        for i, line in enumerate(new_lines):
            stripped = line.strip()
            if stripped.startswith(f"-- {first_char.upper()} ") and "---" in stripped:
                section_start = i + 1
            elif section_start is not None and stripped.startswith("-- ") and "---" in stripped:
                section_end = i
                break

        if section_start is None:
            # Put at end if no section found
            new_lines.append(formatted_line)
            continue

        if section_end is None:
            section_end = len(new_lines)

        # Find the right position within the section (alphabetical)
        insert_at = section_end  # default: end of section
        for i in range(section_start, section_end):
            stripped = new_lines[i].strip()
            if not stripped or not ">" in stripped:
                continue
            existing_term = stripped.split(">")[0].strip().lower()
            if sort_key < existing_term:
                insert_at = i
                break
            elif sort_key == existing_term:
                # Already exists, skip
                insert_at = None
                break

        if insert_at is not None:
            new_lines.insert(insert_at, formatted_line)

    # Write back
    INDEX_FILE.write_text("\n".join(new_lines), encoding="utf-8")

    # Count additions
    original_count = len(lines)
    new_count = len(new_lines)
    print(f"Original lines: {original_count}")
    print(f"New lines: {new_count}")
    print(f"Added: {new_count - original_count} compound term entries")


if __name__ == "__main__":
    main()
