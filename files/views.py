from .models import Download
from django.conf import settings
from django.contrib.auth.decorators import login_required
from django.http import FileResponse, Http404


@login_required
def sendfile(request, path):
    try:
        response = FileResponse(open(settings.MEDIA_ROOT + path, "rb"))
        Download.objects.create(downloader=request.user, path=path)
        return response
    except FileNotFoundError as e:
        raise Http404 from e


def sendfile_nologin(_, path):
    try:
        return FileResponse(open(settings.MEDIA_ROOT + path, "rb"))
    except FileNotFoundError as e:
        raise Http404 from e
