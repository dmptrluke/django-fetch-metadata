from django.test import RequestFactory, SimpleTestCase, override_settings

from fetch_metadata.response import get_violation_response


class TestViolationResponse(SimpleTestCase):
    def setUp(self):
        self.factory = RequestFactory()
        self.request = self.factory.post('/test/')
        self.headers = {'site': 'cross-site', 'mode': 'cors', 'dest': 'empty', 'user': ''}
        self.policy = {'allowed_sites': ['same-origin', 'none'], 'allow_navigations': True, 'fail_open': True}

    @override_settings(DEBUG=True)
    def test_debug_page_rendered_in_debug(self):
        # DEBUG=True renders the debug template with header details
        response = get_violation_response(self.request, 'blocked', self.headers, self.policy)
        self.assertEqual(response.status_code, 403)
        content = response.content.decode()
        self.assertIn('cross-site', content)
        self.assertIn('cors', content)
        self.assertIn('Troubleshooting', content)

    @override_settings(DEBUG=True)
    def test_debug_page_shows_policy(self):
        # debug page includes the active policy
        response = get_violation_response(self.request, 'blocked', self.headers, self.policy)
        content = response.content.decode()
        self.assertIn('same-origin', content)

    @override_settings(DEBUG=False)
    def test_default_403_when_not_debug(self):
        # DEBUG=False returns plain 403
        response = get_violation_response(self.request, 'blocked', self.headers, self.policy)
        self.assertEqual(response.status_code, 403)
        self.assertEqual(response.content, b'Cross-site request blocked.')

    @override_settings(FETCH_METADATA_FAILURE_VIEW='fetch_metadata.tests.urls.failure_view')
    def test_custom_failure_view_called(self):
        # custom failure view receives request, reason, headers
        response = get_violation_response(self.request, 'blocked', self.headers, self.policy)
        self.assertEqual(response.status_code, 403)
        self.assertIn(b'custom 403', response.content)

    @override_settings(FETCH_METADATA_FAILURE_VIEW='fetch_metadata.tests.urls.broken_failure_view', DEBUG=False)
    def test_custom_failure_view_exception_falls_back(self):
        # broken custom view falls back to default 403
        response = get_violation_response(self.request, 'blocked', self.headers, self.policy)
        self.assertEqual(response.status_code, 403)
        self.assertEqual(response.content, b'Cross-site request blocked.')

    @override_settings(DEBUG=True)
    def test_debug_template_is_file_based(self):
        # verify the template is loaded from a file, not inline
        from pathlib import Path

        template_path = Path(__file__).parent.parent / 'templates' / 'fetch_metadata' / '403_debug.html'
        self.assertTrue(template_path.exists())

    @override_settings(DEBUG=True)
    def test_debug_template_render_failure_falls_back(self):
        # broken debug template falls back to plain 403
        from unittest.mock import patch

        with patch('fetch_metadata.response._get_debug_template', side_effect=Exception('template broken')):
            response = get_violation_response(self.request, 'blocked', self.headers, self.policy)
        self.assertEqual(response.status_code, 403)
        self.assertEqual(response.content, b'Cross-site request blocked.')

    @override_settings(FETCH_METADATA_FAILURE_VIEW='fetch_metadata.tests.urls.broken_failure_view', DEBUG=True)
    def test_custom_failure_view_exception_with_debug_shows_debug_page(self):
        # broken custom view + DEBUG=True falls back to debug page (not plain 403)
        from fetch_metadata.response import _get_cached_failure_view

        _get_cached_failure_view.cache_clear()
        response = get_violation_response(self.request, 'blocked', self.headers, self.policy)
        self.assertEqual(response.status_code, 403)
        content = response.content.decode()
        self.assertIn('Troubleshooting', content)

    @override_settings(DEBUG=True)
    def test_debug_page_no_header_strict_reason(self):
        # debug page shows specific troubleshooting for no_header_strict reason
        response = get_violation_response(self.request, 'no_header_strict', self.headers, self.policy)
        content = response.content.decode()
        self.assertIn('FAIL_OPEN', content)
        self.assertIn('Non-browser clients', content)
