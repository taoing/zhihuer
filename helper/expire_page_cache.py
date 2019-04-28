from django.core.cache import cache
from django.http import HttpRequest
from django.urls import reverse
from django.utils.cache import get_cache_key


def expire_page_cache(cur_request, view, args=None, key_prefix=None):
    '''过期由@cache_page生成的缓存页面'''
    if args == None:
        path = reverse(view)
    else:
        path = reverse(view, args=args)

    http_host = cur_request.META.get('HTTP_HOST', '')
    if len(http_host.split(':')) == 1:
        server_name, server_port = http_host, '80'
    else:
        server_name, server_port = http_host.split(':')
    request = HttpRequest()
    request.META = {'SERVER_NAME': server_name, 'SERVER_PORT': server_port}
    request.META.update(dict(
        (header, value) for (header, value) in cur_request.META.items() if
        header.startswith('HTTP_')))
    request.path = path
    key = get_cache_key(request, key_prefix=key_prefix)
    if key and cache.get(key):
        cache.set(key, None, 0)
