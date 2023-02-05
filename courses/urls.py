from django.urls import include, re_path
from . import views

course_patterns = [
    re_path(r"^$", views.info, name="course_info_view"),
    re_path(r"^schedule/$", views.schedule, name="course_schedule_view"),
    re_path(r"^guidelines/$", views.guidelines, name="course_guidelines_view"),
    re_path(r"^assignments/$", views.assignments, name="course_assignments_view"),
    re_path(r"^milestones/$", views.milestones, name="course_milestones_view"),
    re_path(r"^grades/$", views.grades, name="course_grades_view"),
]

urlpatterns = [
    re_path(r"^$", views.index, name="courses_index_view"),
    re_path(
        r"^(?P<slug>[a-z]+(?:-\d+)+)/(?P<year>\d{4})/(?P<semester>sp|su|fa)/",
        include(course_patterns),
    ),
    re_path(
        r"^assignment/(?P<assignment_id>\d+)/submit/$",
        views.submit_assignment,
        name="course_submit_assignment_view",
    ),
]
