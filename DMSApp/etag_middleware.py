import hashlib

class ETagMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        response = self.get_response(request)


        if request.method not in ('GET', 'HEAD'):
            return response

        etag = hashlib.md5(response.content).hexdigest()

        if_none_match = request.headers.get('If-None-Match')

        if if_none_match == etag:

            response.status_code = 304
            response.content = b''

        response['ETag'] = etag

        return response
