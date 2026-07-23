import threading

_local = threading.local()


def get_current_request():
    return getattr(_local, "request", None)


class CurrentUserMiddleware:
    """
    Stashes the current request in thread-local storage so that code
    outside the view layer (model signals, background management
    commands invoked synchronously) can still attribute audit-log
    entries to the acting user when a request is available.
    Views should still prefer passing `request` to log_activity()
    explicitly — this is a fallback, not the primary mechanism.
    """

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        _local.request = request
        try:
            response = self.get_response(request)
        finally:
            _local.request = None
        return response
