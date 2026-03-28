import functools
import logging
from pathlib import Path

from django.conf import settings
from django.http import HttpResponseForbidden
from django.template import Context, Engine
from django.urls import get_callable

logger = logging.getLogger('fetch_metadata')

TEMPLATE_DIR = Path(__file__).parent / 'templates' / 'fetch_metadata'


@functools.cache
def _get_debug_template():
    template_path = TEMPLATE_DIR / '403_debug.html'
    with open(template_path) as f:
        return Engine().from_string(f.read())


def get_violation_response(request, reason, headers, policy):
    """Build the HTTP 403 response for a Fetch Metadata violation."""

    # custom failure view
    failure_view_path = getattr(settings, 'FETCH_METADATA_FAILURE_VIEW', None)
    if failure_view_path:
        try:
            view = _get_cached_failure_view(failure_view_path)
            return view(request, reason=reason, headers=headers)
        except Exception:
            logger.exception(
                'FETCH_METADATA_FAILURE_VIEW %r raised an exception, falling back to default 403', failure_view_path
            )

    # debug page
    if settings.DEBUG:
        try:
            template = _get_debug_template()
            context = Context(
                {
                    'DEBUG': True,
                    'reason': reason,
                    'headers': headers,
                    'policy': policy,
                    'request_method': request.method,
                    'request_path': request.path,
                }
            )
            return HttpResponseForbidden(template.render(context))
        except Exception:
            logger.exception('Failed to render Fetch Metadata debug page')

    return HttpResponseForbidden('Cross-site request blocked.')


@functools.cache
def _get_cached_failure_view(view_path):
    return get_callable(view_path)
