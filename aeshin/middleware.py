from django.http import HttpResponsePermanentRedirect


class WWWRedirectMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        host = request.get_host().partition(":")[0]
        if host == "www.aeshin.org":
            return HttpResponsePermanentRedirect("https://aeshin.org" + request.path)
        else:
            return self.get_response(request)
