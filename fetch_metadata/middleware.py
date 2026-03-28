import logging

from django.utils.cache import patch_vary_headers
from django.utils.deprecation import MiddlewareMixin

from fetch_metadata.conf import get_config
from fetch_metadata.response import get_violation_response

logger = logging.getLogger('fetch_metadata')

# Sec-Fetch-* header names in META format
HEADER_SITE = 'HTTP_SEC_FETCH_SITE'
HEADER_MODE = 'HTTP_SEC_FETCH_MODE'
HEADER_DEST = 'HTTP_SEC_FETCH_DEST'
HEADER_USER = 'HTTP_SEC_FETCH_USER'

SAFE_METHODS = frozenset(('GET', 'HEAD'))

# Sec-Fetch-Dest values that look like navigations but enable cross-site
# embedding. The web.dev reference policy explicitly excludes these from
# the navigation exemption.
UNSAFE_NAVIGATION_DESTS = frozenset(('object', 'embed'))


class FetchMetadataMiddleware(MiddlewareMixin):
    """Resource isolation policy using Fetch Metadata request headers.

    Evaluates every request against a configurable policy based on
    Sec-Fetch-Site and Sec-Fetch-Mode headers. Blocks cross-site
    requests that don't match the active policy.
    """

    def process_response(self, request, response):
        patch_vary_headers(response, ['Sec-Fetch-Site', 'Sec-Fetch-Mode', 'Sec-Fetch-Dest'])
        return response

    def process_view(self, request, callback, callback_args, callback_kwargs):
        result = self._evaluate(request, callback)
        request._fetch_metadata = result

        if result['allowed']:
            return None

        # violation path
        headers = result['headers']
        logger.warning(
            'Fetch Metadata violation: %s %s - Site=%s Mode=%s Dest=%s User=%s reason=%s',
            request.method,
            request.path,
            headers.get('site', '-'),
            headers.get('mode', '-'),
            headers.get('dest', '-'),
            headers.get('user', '-'),
            result['reason'],
        )

        if get_config('REPORT_ONLY'):
            result['report_only'] = True
            return None

        return get_violation_response(request, result['reason'], headers, result['policy'])

    def _evaluate(self, request, callback):
        """Evaluate request against the active policy.

        Returns a dict with: allowed (bool), reason (str),
        policy (dict), headers (dict).
        """
        headers = {
            'site': request.META.get(HEADER_SITE, ''),
            'mode': request.META.get(HEADER_MODE, ''),
            'dest': request.META.get(HEADER_DEST, ''),
            'user': request.META.get(HEADER_USER, ''),
        }

        def _result(allowed, reason, policy=None):
            return {
                'allowed': allowed,
                'reason': reason,
                'policy': policy or {},
                'headers': headers,
                'report_only': False,
            }

        # 1. OPTIONS always pass (CORS preflight)
        if request.method == 'OPTIONS':
            return _result(True, 'options')

        # 2. @fetch_metadata_exempt on view
        if getattr(callback, 'fetch_metadata_exempt', False):
            return _result(True, 'exempt')

        # 3. Path in EXEMPT_PATHS
        exempt_paths = get_config('EXEMPT_PATHS')
        for path_prefix in exempt_paths:
            if request.path.startswith(path_prefix):
                return _result(True, 'exempt_path')

        # 4. Resolve policy: per-view override or global config
        view_policy = getattr(callback, 'fetch_metadata_policy', None)
        if view_policy:
            allowed_sites = view_policy.get('ALLOWED_SITES', get_config('ALLOWED_SITES'))
            allow_navigations = view_policy.get('ALLOW_NAVIGATIONS', get_config('ALLOW_NAVIGATIONS'))
            allow_safe_methods = view_policy.get('ALLOW_SAFE_METHODS', get_config('ALLOW_SAFE_METHODS'))
            fail_open = view_policy.get('FAIL_OPEN', get_config('FAIL_OPEN'))
        else:
            allowed_sites = get_config('ALLOWED_SITES')
            allow_navigations = get_config('ALLOW_NAVIGATIONS')
            allow_safe_methods = get_config('ALLOW_SAFE_METHODS')
            fail_open = get_config('FAIL_OPEN')

        policy = {
            'allowed_sites': allowed_sites,
            'allow_navigations': allow_navigations,
            'allow_safe_methods': allow_safe_methods,
            'fail_open': fail_open,
        }

        # 5. No Sec-Fetch-Site header (or empty)
        site = headers['site']
        if not site:
            if fail_open:
                return _result(True, 'no_header', policy)
            return _result(False, 'no_header_strict', policy)

        # 6. Site in allowed_sites
        if site in allowed_sites:
            return _result(True, 'allowed_site', policy)

        # 7. Safe method exemption: GET/HEAD pass regardless of site
        if allow_safe_methods and request.method in SAFE_METHODS:
            return _result(True, 'safe_method', policy)

        # 8. Navigation exemption: Mode=navigate + safe method + ALLOW_NAVIGATIONS
        # Excludes object/embed dests (cross-site embedding vectors).
        # Also excludes nested-navigate (iframe loads).
        mode = headers['mode']
        dest = headers['dest']
        if (
            allow_navigations
            and mode == 'navigate'
            and request.method in SAFE_METHODS
            and dest not in UNSAFE_NAVIGATION_DESTS
        ):
            return _result(True, 'navigation', policy)

        # 9. Violation
        return _result(False, 'blocked', policy)
