from rest_framework import authentication


class ExampleAuthentication(authentication.BaseAuthentication):
    def authenticate(self, request):
        return request._request.user, None
