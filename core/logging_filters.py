import logging


class RequireExceptionInfo(logging.Filter):
    """Blocks log records that don't carry a real traceback.

    Django's log_response() logs every 5xx response at ERROR level via the
    'django.request' logger, even deliberate ones (e.g. ComingSoonMiddleware's
    503 maintenance page). Without this filter, bots probing random paths
    while maintenance mode is on would email ADMINS once per request.
    """

    def filter(self, record):
        return record.exc_info is not None
