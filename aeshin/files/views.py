from models import Download
from django.conf import settings
from django.contrib.auth.decorators import login_required
from django.http import HttpResponse, Http404

@login_required
def sendfile(request, path):
    if path.endswith('.pdf'):
        response = HttpResponse(content_type='application/pdf')
    elif path.endswith('.zip'):
        response = HttpResponse(content_type='application/zip')
    elif path.endswith('.html'):
        response = HttpResponse(content_type='text/html')
    elif path.endswith('.doc'):
        response = HttpResponse(content_type='application/msword')
    elif path.endswith('.docx'):
        response = HttpResponse(content_type='application/vnd.openxmlformats-officedocument.wordprocessingml.document')
    else:
        raise Http404
    Download.objects.create(downloader=request.user, path=path)
    response['X-Accel-Redirect'] = '/%s%s' % (settings.MEDIA_DIR, path)
    return response

