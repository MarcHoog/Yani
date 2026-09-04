"""Node labels and allowed edges. Starter set from docs/architecture.md section 2."""

LABELS: list[str] = [
    "Customer",
    "Site",
    "Tenant",
    "Employee",
    "EntraUser",
    "Group",
    "Device",
]

# (from_label, relation_type, to_label)
RELATION_CATALOG: list[tuple[str, str, str]] = [
    ("Customer", "HAS_SITE", "Site"),
    ("Customer", "HAS_TENANT", "Tenant"),
    ("Customer", "EMPLOYS", "Employee"),
    ("Employee", "HAS_ACCOUNT", "EntraUser"),
    ("Employee", "OWNS", "Device"),
    ("EntraUser", "IN_TENANT", "Tenant"),
    ("EntraUser", "MEMBER_OF", "Group"),
    ("Group", "IN_TENANT", "Tenant"),
    ("Device", "JOINED_TO", "Tenant"),
    ("Device", "LOCATED_AT", "Site"),
]

RELATION_TYPES: list[str] = sorted({r for _, r, _ in RELATION_CATALOG})


def is_allowed(from_label: str, relation: str, to_label: str) -> bool:
    return (from_label, relation, to_label) in RELATION_CATALOG
