from utils.employee_schema import normalize_text


STUDENT_ID_MAX_LENGTH = 8
STUDENT_NAME_MAX_LENGTH = 80
COURSE_NAME_MAX_LENGTH = 100
STUDENT_CREATE_LOCK_NAME = "students.create"
VALID_STUDENT_STATUSES = {"Inside", "Outside"}
VALID_STUDENT_TYPES = {"Regular", "Irregular"}


def normalize_student_id(value):
    return normalize_text(value).upper()


def normalize_student_name(value):
    return normalize_text(value)


def normalize_course_name(value):
    return normalize_text(value)


def normalize_student_status(value, default="Outside"):
    normalized = normalize_text(value).lower()
    if normalized == "inside":
        return "Inside"
    if normalized == "outside":
        return "Outside"
    return default


def normalize_student_type(value):
    normalized = normalize_text(value).lower()
    if normalized == "regular":
        return "Regular"
    if normalized == "irregular":
        return "Irregular"
    return ""


def validate_student_type(value):
    if normalize_student_type(value):
        return []
    return ["Student Type is required. Choose Regular or Irregular."]


def validate_student_fields(student_id, student_name):
    errors = []
    normalized_student_id = normalize_student_id(student_id)
    normalized_student_name = normalize_student_name(student_name)

    if not normalized_student_id:
        errors.append("Student ID is required.")
    if len(normalized_student_id) > STUDENT_ID_MAX_LENGTH:
        errors.append(
            f"Student ID must be {STUDENT_ID_MAX_LENGTH} characters or fewer."
        )

    if not normalized_student_name:
        errors.append("Student Name is required.")
    if len(normalized_student_name) > STUDENT_NAME_MAX_LENGTH:
        errors.append(
            f"Student Name must be {STUDENT_NAME_MAX_LENGTH} characters or fewer."
        )

    return errors


def validate_course_name(value):
    normalized_course_name = normalize_course_name(value)
    if len(normalized_course_name) > COURSE_NAME_MAX_LENGTH:
        return [f"Course must be {COURSE_NAME_MAX_LENGTH} characters or fewer."]
    return []
