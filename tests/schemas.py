PATIENT = {
    "type": "object",
    "required": ["id", "mrn", "first_name", "last_name", "birth_year"],
    "additionalProperties": False,
    "properties": {
        "id": {"type": "integer", "minimum": 1},
        "mrn": {"type": "string", "pattern": "^SYN\\d{6}$"},
        "first_name": {"type": "string", "minLength": 1},
        "last_name": {"type": "string", "minLength": 1},
        "birth_year": {"type": "integer", "minimum": 1900, "maximum": 2026},
    },
}
PATIENT_PAGE = {
    "type": "object",
    "required": ["page", "size", "total", "items"],
    "properties": {
        "page": {"type": "integer"},
        "size": {"type": "integer"},
        "total": {"type": "integer"},
        "items": {"type": "array", "items": PATIENT},
    },
}
PRESCRIPTION = {
    "type": "object",
    "required": ["id", "drug_code", "drug_name", "quantity", "refills_remaining", "status"],
    "properties": {
        "id": {"type": "integer"},
        "drug_code": {"type": "string", "pattern": "^DRG-\\d{3}$"},
        "drug_name": {"type": "string"},
        "quantity": {"type": "integer", "minimum": 1},
        "refills_remaining": {"type": "integer", "minimum": 0},
        "status": {"enum": ["PENDING", "FILLED", "PICKED_UP", "CANCELLED"]},
    },
}
