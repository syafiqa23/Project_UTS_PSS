from django.contrib import admin
from .models import Course, CourseMember, CourseContent, Comment

@admin.register(Course)
class CourseAdmin(admin.ModelAdmin):
    list_display = ("id", "name", "price", "teacher", "created_at")
    list_filter = ("teacher",)
    search_fields = ("name", "description", "teacher__username")


@admin.register(CourseMember)
class CourseMemberAdmin(admin.ModelAdmin):
    list_display = ("id", "course_id", "user_id", "roles", "created_at")
    list_filter = ("roles", "course_id")
    search_fields = ("course_id__name", "user_id__username")


@admin.register(CourseContent)
class CourseContentAdmin(admin.ModelAdmin):
    list_display = ("id", "name", "course_id", "parent_id", "created_at")
    list_filter = ("course_id",)
    search_fields = ("name", "description", "course_id__name")


@admin.register(Comment)
class CommentAdmin(admin.ModelAdmin):
    list_display = ("id", "content_id", "member_id", "created_at")
    search_fields = ("comment", "content_id__name", "member_id__user_id__username")
