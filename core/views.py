from django.contrib.auth.decorators import login_required
from django.contrib.admin.views.decorators import staff_member_required
from django.contrib.auth.models import User
from django.db.models import Avg, Count, Max, Min, Prefetch
from django.http import HttpResponseBadRequest, HttpResponseForbidden
from django.shortcuts import get_object_or_404, redirect, render
from django.contrib import messages
from django.contrib.auth.views import redirect_to_login
from .services.import_csv_service import import_courses, import_users, import_members

from .models import Comment, Course, CourseContent, CourseMember


def core(request):
    popular_courses = (
        Course.objects.select_related("teacher")
        .annotate(member_count=Count("coursemember"))
        .order_by("-member_count", "name")[:3]
    )
    context = {
        "total_courses": Course.objects.count(),
        "total_users": User.objects.count(),
        "total_comments": Comment.objects.count(),
        "popular_courses": popular_courses,
    }
    return render(request, "core/home.html", context)


def users(request):
    myusers = User.objects.order_by("username")
    return render(request, "core/all_users.html", {"myusers": myusers})


def course_list(request):
    courses = (
        Course.objects.select_related("teacher")
        .annotate(member_count=Count("coursemember", distinct=True), content_count=Count("coursecontent", distinct=True))
        .order_by("name")
    )
    return render(request, "core/all_courses.html", {"courses": courses})


def course_detail(request, course_id):
    course = get_object_or_404(
        Course.objects.select_related("teacher").annotate(
            member_count=Count("coursemember", distinct=True),
            content_count=Count("coursecontent", distinct=True),
        ),
        pk=course_id,
    )
    contents = CourseContent.objects.filter(course_id=course, parent_id__isnull=True).order_by("id")
    is_member = course.can_view(request.user)
    return render(
        request,
        "core/course_detail.html",
        {"course": course, "contents": contents, "is_member": is_member},
    )


@login_required(login_url="/login/")
def join_course(request, course_id):
    course = get_object_or_404(Course, pk=course_id)
    CourseMember.objects.get_or_create(course_id=course, user_id=request.user, defaults={"roles": "std"})
    return redirect("course_detail", course_id=course.id)


@login_required(login_url="/login/")
def my_courses(request):
    memberships = (
        CourseMember.objects.filter(user_id=request.user)
        .select_related("course_id", "course_id__teacher")
        .order_by("course_id__name")
    )
    return render(request, "core/my_courses.html", {"memberships": memberships})


def course_content_list(request, course_id):
    course = get_object_or_404(Course.objects.select_related("teacher"), pk=course_id)
    if not request.user.is_authenticated:
        return redirect_to_login(request.get_full_path(), login_url="login")

    can_view = course.can_view(request.user)
    if not course.can_view(request.user):
        return render(request, "core/course_content_list.html", {
            "course": course,
            "contents": CourseContent.objects.none(),
            "can_view": can_view,
        })

    contents = (
        CourseContent.objects.filter(course_id=course)
        .select_related("course_id", "parent_id")
        .order_by("parent_id__id", "id")
    )

    return render(request, "core/course_content_list.html", {
    "course": course,
    "contents": contents,
    "can_view": can_view
    })


def course_content_detail(request, content_id):
    content = get_object_or_404(
        CourseContent.objects.select_related("course_id", "course_id__teacher", "parent_id"),
        pk=content_id,
    )
    if not request.user.is_authenticated:
        return redirect_to_login(request.get_full_path(), login_url="login")

    if not content.course_id.can_view(request.user):
        messages.warning(request, "Anda harus bergabung dengan course untuk melihat konten.")
        return redirect("course_detail", course_id=content.course_id.id)
    comments = (
        Comment.objects.filter(content_id=content)
        .select_related("member_id", "member_id__user_id")
        .order_by("-created_at")
    )
    course = content.course_id

    can_view = course.can_view(request.user)
    can_assist = course.can_assist(request.user)

    return render(request, "core/course_content_detail.html", {
    "content": content,
    "comments": comments,
    "can_view": can_view,
    "can_assist": can_assist
})

@login_required(login_url="/login/")
def edit_content(request, content_id):
    content = get_object_or_404(CourseContent, pk=content_id)
    course = content.course_id

    # Hanya admin, pengajar, atau asisten yang boleh mengedit konten.
    if not course.can_assist(request.user):
        return HttpResponseForbidden("Tidak punya akses")

    if request.method == "POST":
        content.name = request.POST.get("name")
        content.description = request.POST.get("description")
        content.video_url = request.POST.get("video_url")
        content.save()

        return redirect("course_content_detail", content_id=content.id)

    return render(request, "core/edit_content.html", {"content": content})

@login_required(login_url="/login/")
def add_comment(request, content_id):
    content = get_object_or_404(CourseContent.objects.select_related("course_id"), pk=content_id)
    course = content.course_id

    if not course.can_view(request.user):
        return HttpResponseForbidden("Tidak boleh komentar")
    
    member, _ = CourseMember.objects.get_or_create(
        course_id=course,
        user_id=request.user,
        defaults={"roles": "std"},
    )

    if request.method == "POST":
        comment_text = request.POST.get("comment", "").strip()
        if not comment_text:
            return HttpResponseBadRequest("Komentar tidak boleh kosong.")
        Comment.objects.create(content_id=content, member_id=member, comment=comment_text)
        return redirect("course_content_detail", content_id=content.id)

    return render(request, "core/add_comment.html", {"content": content})

@login_required(login_url="/login/")
def dashboard(request):
    user = request.user

    courses_joined = CourseMember.objects.filter(user_id=user).select_related("course_id")

    total_courses = courses_joined.count()
    total_comments = Comment.objects.filter(member_id__user_id=user).count()

    return render(request, "core/dashboard.html", {
        "courses": courses_joined,
        "total_courses": total_courses,
        "total_comments": total_comments,
    })


def statistik(request):
    return render(request, "core/statistik.html", _get_statistics_context())


def statistik_from_api(request):
    return render(request, "core/statistik_from_api.html", _get_statistics_context())


def _get_course_statistics():
    courses = Course.objects.select_related("teacher")
    stats = courses.aggregate(max_price=Max("price"), min_price=Min("price"), avg_price=Avg("price"))
    annotated_courses = courses.annotate(
        member_count=Count("coursemember", distinct=True),
        content_count=Count("coursecontent", distinct=True),
    )

    return {
        "course_count": courses.count(),
        "content_count": CourseContent.objects.count(),
        "member_count": CourseMember.objects.count(),
        "comment_count": Comment.objects.count(),
        "price_statistics": stats,
        "cheapest": annotated_courses.filter(price=stats["min_price"]).order_by("name"),
        "expensive": annotated_courses.filter(price=stats["max_price"]).order_by("name"),
        "popular": annotated_courses.order_by("-member_count", "name")[:5],
        "unpopular": annotated_courses.order_by("member_count", "name")[:5],
        "courses": annotated_courses.order_by("name"),
    }


def _get_user_statistics():
    non_admin_users = User.objects.filter(is_staff=False, is_superuser=False).order_by("username")
    users_with_courses = non_admin_users.filter(coursemember__isnull=False).distinct()
    users_without_courses = non_admin_users.exclude(id__in=users_with_courses.values("id"))

    avg_courses_per_user = (
        CourseMember.objects.values("user_id")
        .annotate(total=Count("course_id"))
        .aggregate(avg_courses=Avg("total"))["avg_courses"]
        or 0
    )

    top_member = (
        CourseMember.objects.values("user_id", "user_id__username", "user_id__email")
        .annotate(total=Count("course_id"))
        .order_by("-total", "user_id__username")
        .first()
    )
    top_commenter = (
        Comment.objects.values(
            "member_id__user_id",
            "member_id__user_id__username",
            "member_id__user_id__email",
        )
        .annotate(total_comments=Count("id"))
        .order_by("-total_comments", "member_id__user_id__username")
        .first()
    )

    return {
        "total_non_admin_users": non_admin_users.count(),
        "total_users_with_courses": users_with_courses.count(),
        "total_users_without_courses": users_without_courses.count(),
        "average_courses_per_user": avg_courses_per_user,
        "top_user": {
            "username": top_member["user_id__username"],
            "email": top_member["user_id__email"],
            "total_courses": top_member["total"],
        }
        if top_member
        else None,
        "users_no_courses": users_without_courses,
        "total_comments_all": Comment.objects.count(),
        "total_comments_non_admin": Comment.objects.filter(member_id__user_id__in=non_admin_users).count(),
        "top_commenter": {
            "username": top_commenter["member_id__user_id__username"],
            "email": top_commenter["member_id__user_id__email"],
            "total_comments": top_commenter["total_comments"],
        }
        if top_commenter
        else None,
    }


def _get_statistics_context():
    return {
        "course_stats": _get_course_statistics(),
        "user_stats": _get_user_statistics(),
    }


def courseStat(request):
    return render(request, "core/course_stat.html", {"course_stats": _get_course_statistics()})


def userStatistics(request):
    return render(request, "core/user_statistics.html", {"user_stats": _get_user_statistics()})


def api_courses(request):
    courses = (
        Course.objects.select_related("teacher")
        .prefetch_related(
            Prefetch("coursecontent_set", queryset=CourseContent.objects.order_by("id")),
            Prefetch("coursemember_set", queryset=CourseMember.objects.select_related("user_id")),
        )
        .annotate(member_count=Count("coursemember", distinct=True), content_count=Count("coursecontent", distinct=True))
        .order_by("name")
    )
    return render(request, "core/api_courses.html", {"courses": courses})

@staff_member_required(login_url="/admin/login/")
def upload_csv(request):
    if request.method == 'POST':
        file = request.FILES.get('file')
        tipe = request.POST.get('type')

        if not file:
            messages.error(request, "File belum dipilih")
            return render(request, 'core/upload_csv.html')

        try:
            if tipe == 'users':
                created, updated, skipped = import_users(file)
            elif tipe == 'members':
                created, updated, skipped = import_members(file)
            elif tipe == 'courses':
                created, updated, skipped = import_courses(file)
            else:
                messages.error(request, "Tipe tidak valid")
                return render(request, 'core/upload_csv.html')
        except (UnicodeDecodeError, ValueError) as exc:
            messages.error(request, f"Import gagal: {exc}")
            return render(request, 'core/upload_csv.html')

        messages.success(request, f"Import berhasil | Created: {created}, Updated: {updated}, Skipped: {skipped}")

    return render(request, 'core/upload_csv.html')
