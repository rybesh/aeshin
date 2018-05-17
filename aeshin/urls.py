from django import http
from django.urls import include, path, re_path
from django.contrib.auth.decorators import login_required
from django.shortcuts import redirect
from django.template import RequestContext, loader
from django.views.generic.base import TemplateView, RedirectView
from django.contrib import admin
from django.conf import settings
from django.conf.urls.static import static

admin.autodiscover()


@login_required
def loggedin(request):
    if request.user.is_staff:
        return redirect('/admin/')
    for course in request.user.courses.all()[:1]:
        return redirect(course)
    return redirect('/')


def server_error(request, template_name='500.html'):
    t = loader.get_template(template_name)
    return http.HttpResponseServerError(t.render(RequestContext(request, {})))


handler500 = server_error


urlpatterns = [
    re_path(
        r'^$',
        TemplateView.as_view(template_name='bio.html')),
    re_path(
        r'^dissertation/$',
        TemplateView.as_view(template_name='dissertation.html')),
    re_path(
        r'^dhmeetsi/$',
        TemplateView.as_view(template_name='dhmeetsi.html')),
    re_path(
        r'^writing/$',
        TemplateView.as_view(template_name='writing.html')),
    re_path(
        r'^advising/$',
        TemplateView.as_view(template_name='advising.html')),
    re_path(
        r'^favicon.ico$',
        RedirectView.as_view(url='/static/favicon.ico')),
    re_path(
        r'^teaching/',
        include('courses.urls')),
    re_path(
        r'^courses/(?P<path>.*)$',
        RedirectView.as_view(url='/teaching/%(path)s')),
    re_path(
        r'^files/',
        include('files.urls')),
    re_path(
        r'^admin/',
        admin.site.urls),
    re_path(
        r'^loggedin/$',
        loggedin),
    path(
        r'',
        include('django.contrib.auth.urls')),
    re_path(
        r'^rcrforum/$',
        RedirectView.as_view(url='/textmining/')),
    re_path(
        r'^media/img/(?P<path>.*)$',
        RedirectView.as_view(url='/static/%(path)s')),

] + (static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
     if settings.DEBUG else [])
