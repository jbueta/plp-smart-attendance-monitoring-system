import re
import unicodedata


EMPLOYEE_ID_PREFIX = "EMP-"
EMPLOYEE_ID_PAD_WIDTH = 4
EMPLOYEE_NAME_MAX_LENGTH = 80
POSITION_MAX_LENGTH = 100
DEPARTMENT_NAME_MAX_LENGTH = 255
EMPLOYEE_CREATE_LOCK_NAME = "employees.create"
DEPARTMENT_NAME_ALIASES = {
    "COLLEGE OF COMPUTER STUDIES": "COLLEGE OF INFORMATION TECHNOLOGY",
    "COLLEGE OF COMPUTER SCIENCE": "COLLEGE OF INFORMATION TECHNOLOGY",
    "COMPUTER STUDIES": "COLLEGE OF INFORMATION TECHNOLOGY",
    "COMPUTER SCIENCE": "COLLEGE OF INFORMATION TECHNOLOGY",
    "INFORMATION TECHNOLOGY": "COLLEGE OF INFORMATION TECHNOLOGY",
    "COLLEGE OF ENGINEERING": "COLLEGE OF ELECTRICAL ENGINEERING",
    "ENGINEERING": "COLLEGE OF ELECTRICAL ENGINEERING",
    "REGISTRAR OFFICE": "REGISTRAR'S OFFICE",
    "HR OFFICE": "HUMAN RESOURCES OFFICE",
    "HUMAN RESOURCE OFFICE": "HUMAN RESOURCES OFFICE",
}


def normalize_text(value):
    if not isinstance(value, str):
        value = str(value) if value is not None else ""

    value = unicodedata.normalize("NFKC", value)
    value = re.sub(r"[\u2018\u2019\u02bc\u0060\u00b4]", "'", value)
    value = re.sub(r"[\u2013\u2014]", "-", value)
    value = value.replace("\u00a0", " ").replace("\u200b", "")
    value = re.sub(r"\s+", " ", value)
    return value.strip()


def normalize_employee_name(value):
    return normalize_text(value)


def normalize_position(value):
    return normalize_text(value)


def normalize_department_name(value):
    return normalize_text(value)


def build_person_name_match_keys(value):
    normalized_name = normalize_text(value).upper()
    if not normalized_name:
        return set()

    compact_name = re.sub(r"[^A-Z0-9]", "", normalized_name)
    keys = {normalized_name}
    if compact_name:
        keys.add(compact_name)
    return keys


def resolve_department_alias(value):
    normalized_department = normalize_department_name(value)
    alias_key = normalized_department.upper()
    return DEPARTMENT_NAME_ALIASES.get(alias_key, normalized_department)


def department_lookup_key(value):
    return resolve_department_alias(value).upper()


def build_employee_signature(employee_name, department_id, position):
    return (
        normalize_employee_name(employee_name).upper(),
        str(department_id or "").strip(),
        normalize_position(position).upper(),
    )


def format_employee_id(seq):
    sequence = max(int(seq or 0), 0)
    return f"{EMPLOYEE_ID_PREFIX}{str(sequence).zfill(EMPLOYEE_ID_PAD_WIDTH)}"


def validate_employee_fields(employee_name, position="", require_position=False):
    errors = []
    normalized_name = normalize_employee_name(employee_name)
    normalized_position = normalize_position(position)

    if not normalized_name:
        errors.append("Employee Name is required.")
    if len(normalized_name) > EMPLOYEE_NAME_MAX_LENGTH:
        errors.append(
            f"Employee Name must be {EMPLOYEE_NAME_MAX_LENGTH} characters or fewer."
        )

    if require_position and not normalized_position:
        errors.append("Position is required.")
    if len(normalized_position) > POSITION_MAX_LENGTH:
        errors.append(f"Position must be {POSITION_MAX_LENGTH} characters or fewer.")

    return errors


def validate_department_name(value):
    normalized_department = normalize_department_name(value)
    if len(normalized_department) > DEPARTMENT_NAME_MAX_LENGTH:
        return [
            f"Department must be {DEPARTMENT_NAME_MAX_LENGTH} characters or fewer."
        ]
    return []
