import csv
import os

from django.contrib.auth.models import User
from django.core.management.base import BaseCommand, CommandError

from core.models import Course, CourseMember


def _read_csv(path, required_columns):
    if not os.path.exists(path):
        raise CommandError(f"File tidak ditemukan: {path}")

    with open(path, newline="", encoding="utf-8-sig") as file:
        reader = csv.DictReader(file)
        headers = set(reader.fieldnames or [])
        missing_columns = [column for column in required_columns if column not in headers]
        if missing_columns:
            raise CommandError("Kolom CSV tidak lengkap: " + ", ".join(missing_columns))

        return [row for row in reader]


class Command(BaseCommand):
    help = "Hapus semua data yang diimport dari users.csv, courses.csv, dan members.csv"

    def add_arguments(self, parser):
        parser.add_argument(
            "--users-csv",
            type=str,
            default=None,
            help="Path file CSV users (default: data/users.csv)",
        )
        parser.add_argument(
            "--courses-csv",
            type=str,
            default=None,
            help="Path file CSV courses (default: data/courses.csv)",
        )
        parser.add_argument(
            "--members-csv",
            type=str,
            default=None,
            help="Path file CSV members (default: data/members.csv)",
        )

    def handle(self, *args, **options):
        cwd = os.getcwd()
        users_path = options["users_csv"] or os.path.join(cwd, "data", "users.csv")
        courses_path = options["courses_csv"] or os.path.join(cwd, "data", "courses.csv")
        members_path = options["members_csv"] or os.path.join(cwd, "data", "members.csv")

        self.stdout.write(self.style.NOTICE("Membaca file CSV..."))

        users_rows = _read_csv(users_path, ["username", "email", "password", "is_staff"])
        courses_rows = _read_csv(courses_path, ["name", "description", "price", "teacher_username"])
        members_rows = _read_csv(members_path, ["course_name", "username", "role"])

        user_usernames = {row.get("username", "").strip() for row in users_rows if row.get("username")}
        course_names = {row.get("name", "").strip() for row in courses_rows if row.get("name")}
        membership_pairs = {
            (row.get("course_name", "").strip(), row.get("username", "").strip())
            for row in members_rows
            if row.get("course_name") and row.get("username")
        }

        self.stdout.write(self.style.NOTICE("Menghapus CourseMember..."))
        deleted_members = 0
        for course_name, username in membership_pairs:
            deleted_members += CourseMember.objects.filter(
                course_id__name=course_name,
                user_id__username=username,
            ).delete()[0]

        self.stdout.write(self.style.NOTICE("Menghapus Course..."))
        deleted_courses = Course.objects.filter(name__in=course_names).delete()[0]

        self.stdout.write(self.style.NOTICE("Menghapus User..."))
        deleted_users = User.objects.filter(username__in=user_usernames).delete()[0]

        self.stdout.write(self.style.SUCCESS(
            f"Selesai. CourseMember dihapus: {deleted_members}, Course dihapus: {deleted_courses}, User dihapus: {deleted_users}"
        ))
