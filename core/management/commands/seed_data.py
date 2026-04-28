from django.contrib.auth.models import User
from django.core.management.base import BaseCommand

from core.models import Comment, Course, CourseContent, CourseMember


class Command(BaseCommand):
    help = "Seed data simple LMS untuk demo UTS"

    def handle(self, *args, **kwargs):
        self.stdout.write(self.style.SUCCESS("Start seeding LMS..."))

        admin, _ = User.objects.get_or_create(
            username="adminuts",
            defaults={
                "email": "adminuts@example.com",
                "is_staff": True,
                "is_superuser": True,
            },
        )
        admin.email = "adminuts@example.com"
        admin.is_staff = True
        admin.is_superuser = True
        admin.set_password("admin12345")
        admin.save()

        users = []
        user_data = [
            ("pikachu", "pikaimoet@gmail.com", True),
            ("syafiqa", "syafiqa@gmail.com", False),
            ("zahroo", "zahroo@gmail.com", False),
            ("nabila", "nabila@gmail.com", False),
            ("rangga", "rangga@gmail.com", False),
        ]

        for username, email, is_staff in user_data:
            user, _ = User.objects.get_or_create(username=username, defaults={"email": email})
            user.email = email
            user.is_staff = is_staff
            if not user.has_usable_password():
                user.set_password("12345")
            user.save()
            users.append(user)

        self.stdout.write(self.style.SUCCESS("Users created or updated"))

        teacher = users[0]
        course_data = [
            ("PSS", "Pemrograman sisi server dengan Django, ORM, dan Docker.", 10000),
            ("Frontend Development dengan React", "Dasar pengembangan antarmuka web modern.", 275000),
            ("Machine Learning Dasar", "Pengenalan dataset, training, evaluasi, dan deployment sederhana.", 350000),
            ("Bisnis Syacos", "Belajar strategi bisnis kosmetik dari nol.", 30000),
            ("Basis Data Lanjut", "Relasi, indexing, transaksi, dan optimasi query.", 150000),
        ]

        courses = []
        for name, description, price in course_data:
            course, _ = Course.objects.get_or_create(
                name=name,
                defaults={"description": description, "price": price, "teacher": teacher},
            )
            course.description = description
            course.price = price
            course.teacher = teacher
            course.save()
            courses.append(course)

        self.stdout.write(self.style.SUCCESS("Courses created or updated"))

        membership_data = [
            (courses[0], users[0], "ast"),
            (courses[0], users[1], "std"),
            (courses[0], users[2], "std"),
            (courses[1], users[1], "std"),
            (courses[1], users[3], "std"),
            (courses[2], users[2], "std"),
            (courses[2], users[4], "std"),
            (courses[3], users[3], "std"),
        ]

        members = {}
        for course, user, role in membership_data:
            member, _ = CourseMember.objects.get_or_create(
                course_id=course,
                user_id=user,
                defaults={"roles": role},
            )
            member.roles = role
            member.save()
            members[(course.name, user.username)] = member

        self.stdout.write(self.style.SUCCESS("Members created or updated"))

        contents = {}
        for course in courses:
            intro, _ = CourseContent.objects.get_or_create(
                course_id=course,
                name=f"Pengantar {course.name}",
                defaults={
                    "description": f"Materi pembuka untuk mata kuliah {course.name}.",
                    "video_url": "https://youtube.com",
                },
            )
            task, _ = CourseContent.objects.get_or_create(
                course_id=course,
                parent_id=intro,
                name=f"Tugas Praktik {course.name}",
                defaults={
                    "description": "Latihan praktik untuk menguji pemahaman mahasiswa.",
                    "video_url": "https://youtube.com",
                },
            )
            contents[(course.name, "intro")] = intro
            contents[(course.name, "task")] = task

        self.stdout.write(self.style.SUCCESS("Contents created or updated"))

        comment_data = [
            (contents[("PSS", "intro")], members[("PSS", "syafiqa")], "Materinya jelas dan cocok untuk UTS."),
            (contents[("PSS", "task")], members[("PSS", "zahroo")], "Saya sudah coba query annotate di tugas praktik."),
            (
                contents[("Frontend Development dengan React", "intro")],
                members[("Frontend Development dengan React", "syafiqa")],
                "Contoh komponennya mudah dipahami.",
            ),
            (
                contents[("Machine Learning Dasar", "intro")],
                members[("Machine Learning Dasar", "rangga")],
                "Bagian evaluasi model sangat membantu.",
            ),
        ]

        for content, member, comment in comment_data:
            Comment.objects.get_or_create(content_id=content, member_id=member, comment=comment)

        self.stdout.write(self.style.SUCCESS("Comments created or updated"))
        self.stdout.write(self.style.SUCCESS("SEEDING DONE"))
        self.stdout.write("Admin demo: adminuts / admin12345")
        self.stdout.write("User demo: syafiqa / 12345")
