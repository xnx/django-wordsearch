"""The app's settings. A site overrides one by setting WORDSEARCH_<NAME>."""

from django.conf import settings
from django.utils.module_loading import import_string

DEFAULTS = {
    # The maker: the greatest number of rows or columns, of words, and of
    # characters in the list of words. The maker is a GET form, so that the link
    # to a puzzle makes it again; MAX_CHARS keeps that address short enough for
    # servers such as gunicorn, which refuses a request line over 4094 bytes.
    "MAX_SIZE": 32,
    "MAX_WORDS": 150,
    "MAX_CHARS": 1500,
    # Seconds to search for a puzzle before giving up.
    "TIME_LIMIT": 2.0,
    # The solver (a POST form): the greatest number of rows or columns, of
    # words, and of characters in the grid or in the list of words.
    "SOLVER_MAX_SIZE": 50,
    "SOLVER_MAX_WORDS": 200,
    "SOLVER_MAX_CHARS": 10_000,
    # Puzzles that one visitor may make in an hour (None for no limit), counted
    # in Django's default cache.
    "RATE_LIMIT_PER_HOUR": None,
    # The dotted path of a function of the request that returns the visitor's
    # address, for the rate limit; REMOTE_ADDR if None. Behind a proxy, every
    # visitor has the proxy's REMOTE_ADDR, so a site sets this to a function
    # that reads the proxy's header.
    "CLIENT_IP": None,
}


def setting(name):
    return getattr(settings, f"WORDSEARCH_{name}", DEFAULTS[name])


def client_ip(request):
    """The visitor's address, by the function that CLIENT_IP names, if any."""
    path = setting("CLIENT_IP")
    if path:
        return import_string(path)(request)
    return request.META.get("REMOTE_ADDR", "")
