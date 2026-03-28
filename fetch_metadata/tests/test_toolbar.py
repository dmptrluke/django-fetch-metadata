from unittest.mock import MagicMock

from django.template.loader import get_template
from django.test import RequestFactory, SimpleTestCase, override_settings

from fetch_metadata.contrib.toolbar import FetchMetadataPanel


class TestFetchMetadataPanel(SimpleTestCase):
    def _make_panel(self):
        toolbar = MagicMock()
        toolbar.stats = {}
        toolbar.store = MagicMock()
        get_response = MagicMock()
        return FetchMetadataPanel(toolbar, get_response)

    def test_reads_annotation(self):
        # panel reads request._fetch_metadata and records stats
        panel = self._make_panel()
        request = RequestFactory().get('/test/')
        request._fetch_metadata = {
            'allowed': True,
            'reason': 'allowed_site',
            'headers': {'site': 'same-origin', 'mode': 'navigate', 'dest': 'document', 'user': ''},
            'policy': {'allowed_sites': ['same-origin', 'none']},
            'report_only': False,
        }
        response = MagicMock()
        panel.generate_stats(request, response)
        stats = panel.get_stats()
        self.assertTrue(stats['has_data'])
        self.assertEqual(stats['site'], 'same-origin')
        self.assertEqual(stats['reason'], 'allowed_site')
        self.assertTrue(stats['allowed'])

    def test_handles_missing_annotation(self):
        # panel handles request without _fetch_metadata gracefully
        panel = self._make_panel()
        request = RequestFactory().get('/test/')
        response = MagicMock()
        panel.generate_stats(request, response)
        stats = panel.get_stats()
        self.assertFalse(stats['has_data'])

    def test_shows_blocked_decision(self):
        # panel shows blocked status
        panel = self._make_panel()
        request = RequestFactory().post('/test/')
        request._fetch_metadata = {
            'allowed': False,
            'reason': 'blocked',
            'headers': {'site': 'cross-site', 'mode': 'cors', 'dest': 'empty', 'user': ''},
            'policy': {'allowed_sites': ['same-origin', 'none']},
            'report_only': False,
        }
        response = MagicMock()
        panel.generate_stats(request, response)
        stats = panel.get_stats()
        self.assertFalse(stats['allowed'])
        self.assertEqual(stats['reason'], 'blocked')

    def test_nav_subtitle_with_data(self):
        # nav_subtitle shows site and reason
        panel = self._make_panel()
        request = RequestFactory().get('/test/')
        request._fetch_metadata = {
            'allowed': True,
            'reason': 'navigation',
            'headers': {'site': 'cross-site', 'mode': 'navigate', 'dest': 'document', 'user': ''},
            'policy': {},
            'report_only': False,
        }
        response = MagicMock()
        panel.generate_stats(request, response)
        subtitle = panel.nav_subtitle
        self.assertIn('cross-site', subtitle)
        self.assertIn('navigation', subtitle)

    @override_settings(
        TEMPLATES=[
            {
                'BACKEND': 'django.template.backends.django.DjangoTemplates',
                'APP_DIRS': True,
            }
        ]
    )
    def test_template_renders(self):
        # panel template loads from disk and renders without errors
        template = get_template('fetch_metadata/panels/fetch_metadata.html')
        context = {
            'has_data': True,
            'site': 'cross-site',
            'mode': 'cors',
            'dest': 'empty',
            'user': '',
            'allowed': False,
            'reason': 'blocked',
            'report_only': False,
            'policy': {'allowed_sites': ['same-origin', 'none'], 'allow_navigations': True, 'fail_open': True},
        }
        html = template.render(context)
        self.assertIn('cross-site', html)
        self.assertIn('Blocked', html)
