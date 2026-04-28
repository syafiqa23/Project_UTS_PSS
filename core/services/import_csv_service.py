import csv
from django.contrib.auth.models import User
from core.models import Course, CourseMember


def _read_csv(file):
    return csv.DictReader(file.read().decode("utf-8-sig").splitlines())


def _validate_headers(reader, required_columns):
    headers = set(reader.fieldnames or [])
    missing_columns = [column for column in required_columns if column not in headers]
    if missing_columns:
        raise ValueError("Kolom CSV tidak lengkap: " + ", ".join(missing_columns))


def _parse_staff(value):
    return str(value or "0").strip().lower() in {"1", "true", "yes", "y"}


def _parse_price(value):
    try:
        return int(str(value or "0").strip())
    except ValueError:
        return None


def import_users(file):
    created, updated, skipped = 0, 0, 0
    reader = _read_csv(file)
    _validate_headers(reader, ["username", "email", "password", "is_staff"])

    for row in reader:
        username = row.get("username", "").strip()
        if not username:
            skipped += 1
            continue

        obj, is_created = User.objects.update_or_create(
            username=username,
            defaults={
                "email": row.get("email", "").strip(),
                "is_staff": _parse_staff(row.get("is_staff")),
            }
        )

        password = row.get("password", "").strip()
        if password:
            obj.set_password(password)
        elif is_created:
            obj.set_password("12345")
        obj.save()

        if is_created:
            created += 1
        else:
            updated += 1

    return created, updated, skipped


def import_members(file):
    created, updated, skipped = 0, 0, 0
    reader = _read_csv(file)
    _validate_headers(reader, ["course_name", "username", "role"])

    for row in reader:
        username = row.get("username", "").strip()
        course_name = row.get("course_name", "").strip()
        role = row.get("role", "std").strip() or "std"

        if not username or not course_name or role not in {"std", "ast"}:
            skipped += 1
            continue

        try:
            user = User.objects.get(username=username)
            course = Course.objects.get(name=course_name)
        except (User.DoesNotExist, Course.DoesNotExist):
            skipped += 1
            continue

        obj, is_created = CourseMember.objects.update_or_create(
            user_id=user,
            course_id=course,
            defaults={
                "roles": role
            }
        )

        if is_created:
            created += 1
        else:
            updated += 1

    return created, updated, skipped


def import_courses(file):
    created, updated, skipped = 0, 0, 0
    reader = _read_csv(file)
    _validate_headers(reader, ["name", "description", "price", "teacher_username"])

    for row in reader:
        name = row.get("name", "").strip()
        teacher_username = row.get("teacher_username", "").strip()
        price = _parse_price(row.get("price"))

        if not name or not teacher_username or price is None:
            skipped += 1
            continue

        try:
            teacher = User.objects.get(username=teacher_username)
        except User.DoesNotExist:
            skipped += 1
            continue

        obj, is_created = Course.objects.update_or_create(
            name=name,
            defaults={
                "description": row.get("description", "-").strip() or "-",
                "price": price,
                "teacher": teacher
            }
        )

        if is_created:
            created += 1
        else:
            updated += 1

    return created, updated, skipped
