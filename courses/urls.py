from django.conf.urls import patterns, include, url
import views

course_patterns = patterns('',
    url(r'^$',
        views.info, name='course_info_view'),
    url(r'^schedule/$',
        views.schedule, name='course_schedule_view'),
    url(r'^guidelines/$',
        views.guidelines, name='course_guidelines_view'),
    url(r'^thanks/$',
        views.thanks, name='course_thanks_view'),
    url(r'^assignments/$',
        views.assignments, name='course_assignments_view'),
    url(r'^grades/$',
        views.grades, name='course_grades_view'),
)
urlpatterns = patterns('',
    url(r'^$',
        views.index, name='courses_index_view'),
    (r'^(?P<slug>[a-z]+(?:-\d+)+)/(?P<year>\d{4})/(?P<semester>sp|su|fa)/',
        include(course_patterns)),
    url(r'^assignment/(?P<assignment_id>\d+)/submit/$',
        views.submit_assignment, name='course_submit_assignment_view'),
)

