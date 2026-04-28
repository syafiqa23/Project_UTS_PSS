from django.contrib.auth import views as auth_views
from django.urls import path

from . import views

urlpatterns = [
    path(
        "login/",
        auth_views.LoginView.as_view(template_name="core/login.html"),
        name="login",
    ),
    path(
        "logout/",
        auth_views.LogoutView.as_view(next_page="core"),
        name="logout",
    ),
    path("", views.core, name="core"),
    path("home/", views.core, name="home"),
    path("core/", views.core, name="core_legacy"),
    path("users/", views.users, name="users"),
    path("courses/", views.course_list, name="course_list"),
    path("courses/<int:course_id>/", views.course_detail, name="course_detail"),
    path("courses/<int:course_id>/join/", views.join_course, name="join_course"),
    path("courses/<int:course_id>/contents/", views.course_content_list, name="course_content_list"),
    path("contents/<int:content_id>/", views.course_content_detail, name="course_content_detail"),
    path("contents/<int:content_id>/comment/", views.add_comment, name="add_comment"),
    path("my-courses/", views.my_courses, name="my_courses"),
    path("statistik/", views.statistik, name="statistik"),
    path("statistik-api/", views.statistik_from_api, name="statistik_api"),
    path("api/courses/", views.api_courses, name="api_courses"),
    path("api/course-stat/", views.courseStat, name="course_stat"),
    path("api/user-stats/", views.userStatistics, name="user_statistics"),
    path("course-stat/", views.courseStat, name="course_stat_legacy"),
    path("user-stats/", views.userStatistics, name="user_statistics_legacy"),
    path("course/<int:course_id>/", views.course_detail, name="course_detail_legacy"),
    path("course/<int:course_id>/join/", views.join_course, name="join_course_legacy"),
    path("course/<int:course_id>/contents/", views.course_content_list, name="course_content_list_legacy"),
    path("content/<int:content_id>/", views.course_content_detail, name="course_content_detail_legacy"),
    path("content/<int:content_id>/comment/", views.add_comment, name="add_comment_legacy"),
    path('import-csv/', views.upload_csv, name='upload_csv'),
    path('content/<int:content_id>/edit/', views.edit_content, name='edit_content'),
    path('dashboard/', views.dashboard, name='dashboard'),
]
