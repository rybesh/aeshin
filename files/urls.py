from django.conf.urls import re_path
from . import views

urlpatterns = [
    re_path(
        r'^(?P<path>.+(\.pdf|\.zip|\.html|\.doc|\.docx|\.epub))$',
        views.sendfile, name='files_sendfile_view')
]
