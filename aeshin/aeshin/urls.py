from django import http
from django.conf.urls import patterns, include, url
from django.contrib.auth.decorators import login_required
from django.shortcuts import redirect
from django.template import RequestContext, loader
from django.views.generic.base import TemplateView, RedirectView

from django.contrib import admin
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

urlpatterns = patterns('',
    url(r'^deploy/$', 'shared.views.deploy', name='shared_deploy_view'),

    (r'^$', 
     TemplateView.as_view(template_name='bio.html')),
    (r'^dissertation/$', 
     TemplateView.as_view(template_name='dissertation.html')),
    (r'^dhmeetsi/$', 
     TemplateView.as_view(template_name='dhmeetsi.html')),

    (r'^favicon.ico$', 
      RedirectView.as_view(url='/static/favicon.ico')),

    (r'^teaching/', include('courses.urls')),
    (r'^courses/(?P<path>.*)$', 
     RedirectView.as_view(url='/teaching/%(path)s')),
   
    (r'^files/', include('files.urls')),     

    (r'^admin/', include(admin.site.urls)),

    (r'^loggedin/$', loggedin),
    (r'', include('django.contrib.auth.urls')),

    (r'^rcrforum/$', 
     RedirectView.as_view(url='/textmining/')),

    (r'^media/img/(?P<path>.*)$', 
     RedirectView.as_view(url='/static/%(path)s')),
)


