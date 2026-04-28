import csv
import os

from django.contrib.auth.models import User
from django.core.management.base import BaseCommand, CommandError

from core.models import Course


class Command(BaseCommand):
    help = "Import data course dari file CSV"

    def add_arguments(self, parser):
        parser.add_argument(
            "csv_path",
            type=str,
            help="Path file CSV (contoh: data/courses.csv)",
        )

    def handle(self, *args, **options):
        csv_path = options["csv_path"]

        if not os.path.exists(csv_path):
            raise CommandError(f"File tidak ditemukan: {csv_path}")

        created = 0
        updated = 0
        skipped = 0

        with open(csv_path, newline="", encoding="utf-8-sig") as file:
            reader = csv.DictReader(file)
            required_columns = {"name", "description", "price", "teacher_username"}
            missing_columns = required_columns.difference(reader.fieldnames or [])
            if missing_columns:
                raise CommandError("Kolom CSV tidak lengkap: " + ", ".join(sorted(missing_columns)))

            for row_number, row in enumerate(reader, start=2):
                name = row.get("name", "").strip()
                teacher_username = row.get("teacher_username", "").strip()

                try:
                    price = int(str(row.get("price", "0")).strip())
                except ValueError:
                    skipped += 1
                    self.stdout.write(self.style.WARNING(f"Baris {row_number} dilewati: harga tidak valid."))
                    continue

                if not name or not teacher_username:
                    skipped += 1
                    self.stdout.write(self.style.WARNING(f"Baris {row_number} dilewati: nama/teacher kosong."))
                    continue

                try:
                    teacher = User.objects.get(username=teacher_username)
                except User.DoesNotExist:
                    skipped += 1
                    self.stdout.write(
                        self.style.WARNING(f"Baris {row_number} dilewati: user {teacher_username} tidak ditemukan.")
                    )
                    continue

                obj, is_created = Course.objects.update_or_create(
                    name=name,
                    defaults={
                        "description": row.get("description", "-").strip() or "-",
                        "price": price,
                        "teacher": teacher,
                    },
                )

                if is_created:
                    created += 1
                else:
                    updated += 1

        self.stdout.write(
            self.style.SUCCESS(f"Import selesai | Created: {created}, Updated: {updated}, Skipped: {skipped}")
        )
