from django.test import RequestFactory, SimpleTestCase, override_settings

from fetch_metadata.middleware import FetchMetadataMiddleware


def _get_response(request):
    pass


def _make_middleware():
    return FetchMetadataMiddleware(_get_response)


def _dummy_view(request):
    pass


def _exempt_view(request):
    pass


_exempt_view.fetch_metadata_exempt = True


def _policy_view(request):
    pass


_policy_view.fetch_metadata_policy = {
    'ALLOWED_SITES': ['same-origin', 'same-site'],
}


class TestOptionsPassThrough(SimpleTestCase):
    """OPTIONS requests always pass (CORS preflight)."""

    def test_options_cross_site(self):
        # OPTIONS passes even with cross-site header
        factory = RequestFactory()
        request = factory.options('/test/', HTTP_SEC_FETCH_SITE='cross-site', HTTP_SEC_FETCH_MODE='cors')
        mw = _make_middleware()
        result = mw.process_view(request, _dummy_view, (), {})
        self.assertIsNone(result)
        self.assertTrue(request._fetch_metadata['allowed'])
        self.assertEqual(request._fetch_metadata['reason'], 'options')


class TestMissingHeaders(SimpleTestCase):
    """Behavior when Sec-Fetch-Site header is not present."""

    def test_missing_header_default_passes(self):
        # DEFAULT preset: fail-open, missing header passes
        factory = RequestFactory()
        request = factory.post('/test/')
        mw = _make_middleware()
        result = mw.process_view(request, _dummy_view, (), {})
        self.assertIsNone(result)
        self.assertTrue(request._fetch_metadata['allowed'])
        self.assertEqual(request._fetch_metadata['reason'], 'no_header')

    @override_settings(FETCH_METADATA_PRESET='STRICT')
    def test_missing_header_strict_blocks(self):
        # STRICT preset: fail-closed, missing header blocked
        factory = RequestFactory()
        request = factory.post('/test/')
        mw = _make_middleware()
        result = mw.process_view(request, _dummy_view, (), {})
        self.assertIsNotNone(result)
        self.assertEqual(result.status_code, 403)

    def test_empty_header_treated_as_unknown(self):
        # empty Sec-Fetch-Site is not fail-open, it's an unknown value
        factory = RequestFactory()
        request = factory.post('/test/', HTTP_SEC_FETCH_SITE='')
        mw = _make_middleware()
        result = mw.process_view(request, _dummy_view, (), {})
        self.assertIsNone(result)
        # empty string is falsy, hits the no-header path
        self.assertTrue(request._fetch_metadata['allowed'])


class TestAllowedSites(SimpleTestCase):
    """Requests with Sec-Fetch-Site values in the allowed list pass."""

    def test_same_origin_passes(self):
        factory = RequestFactory()
        request = factory.post('/test/', HTTP_SEC_FETCH_SITE='same-origin', HTTP_SEC_FETCH_MODE='cors')
        mw = _make_middleware()
        result = mw.process_view(request, _dummy_view, (), {})
        self.assertIsNone(result)
        self.assertTrue(request._fetch_metadata['allowed'])
        self.assertEqual(request._fetch_metadata['reason'], 'allowed_site')

    def test_none_passes(self):
        # 'none' = direct navigation (typing URL, bookmark)
        factory = RequestFactory()
        request = factory.post('/test/', HTTP_SEC_FETCH_SITE='none', HTTP_SEC_FETCH_MODE='navigate')
        mw = _make_middleware()
        result = mw.process_view(request, _dummy_view, (), {})
        self.assertIsNone(result)
        self.assertTrue(request._fetch_metadata['allowed'])

    def test_cross_site_blocked(self):
        factory = RequestFactory()
        request = factory.post('/test/', HTTP_SEC_FETCH_SITE='cross-site', HTTP_SEC_FETCH_MODE='cors')
        mw = _make_middleware()
        result = mw.process_view(request, _dummy_view, (), {})
        self.assertIsNotNone(result)
        self.assertEqual(result.status_code, 403)

    def test_same_site_blocked_under_default(self):
        # same-site (subdomain) not in DEFAULT allowed list
        factory = RequestFactory()
        request = factory.post('/test/', HTTP_SEC_FETCH_SITE='same-site', HTTP_SEC_FETCH_MODE='cors')
        mw = _make_middleware()
        result = mw.process_view(request, _dummy_view, (), {})
        self.assertIsNotNone(result)
        self.assertEqual(result.status_code, 403)

    def test_unknown_site_value_blocked(self):
        # unknown/garbage value treated as hostile
        factory = RequestFactory()
        request = factory.post('/test/', HTTP_SEC_FETCH_SITE='evil-site', HTTP_SEC_FETCH_MODE='cors')
        mw = _make_middleware()
        result = mw.process_view(request, _dummy_view, (), {})
        self.assertIsNotNone(result)
        self.assertEqual(result.status_code, 403)

    @override_settings(FETCH_METADATA_ALLOWED_SITES=['same-origin', 'same-site', 'none'])
    def test_custom_allowed_sites(self):
        # explicit setting overrides preset
        factory = RequestFactory()
        request = factory.post('/test/', HTTP_SEC_FETCH_SITE='same-site', HTTP_SEC_FETCH_MODE='cors')
        mw = _make_middleware()
        result = mw.process_view(request, _dummy_view, (), {})
        self.assertIsNone(result)
        self.assertTrue(request._fetch_metadata['allowed'])


class TestNavigationExemption(SimpleTestCase):
    """Cross-site navigations (link clicks) handled by ALLOW_NAVIGATIONS."""

    def test_cross_site_navigate_get_allowed(self):
        # cross-site link click: Mode=navigate + GET = allowed under DEFAULT
        factory = RequestFactory()
        request = factory.get('/test/', HTTP_SEC_FETCH_SITE='cross-site', HTTP_SEC_FETCH_MODE='navigate')
        mw = _make_middleware()
        result = mw.process_view(request, _dummy_view, (), {})
        self.assertIsNone(result)
        self.assertTrue(request._fetch_metadata['allowed'])
        self.assertEqual(request._fetch_metadata['reason'], 'navigation')

    def test_cross_site_navigate_post_blocked(self):
        # cross-site form POST: Mode=navigate + POST = blocked even with ALLOW_NAVIGATIONS
        factory = RequestFactory()
        request = factory.post('/test/', HTTP_SEC_FETCH_SITE='cross-site', HTTP_SEC_FETCH_MODE='navigate')
        mw = _make_middleware()
        result = mw.process_view(request, _dummy_view, (), {})
        self.assertIsNotNone(result)
        self.assertEqual(result.status_code, 403)

    def test_cross_site_navigate_head_allowed(self):
        # HEAD + navigate also allowed (safe method)
        factory = RequestFactory()
        request = factory.head('/test/', HTTP_SEC_FETCH_SITE='cross-site', HTTP_SEC_FETCH_MODE='navigate')
        mw = _make_middleware()
        result = mw.process_view(request, _dummy_view, (), {})
        self.assertIsNone(result)
        self.assertTrue(request._fetch_metadata['allowed'])

    @override_settings(FETCH_METADATA_PRESET='API')
    def test_cross_site_navigate_blocked_api_preset(self):
        # API preset: ALLOW_NAVIGATIONS=False, navigation GET blocked
        factory = RequestFactory()
        request = factory.get('/test/', HTTP_SEC_FETCH_SITE='cross-site', HTTP_SEC_FETCH_MODE='navigate')
        mw = _make_middleware()
        result = mw.process_view(request, _dummy_view, (), {})
        self.assertIsNotNone(result)
        self.assertEqual(result.status_code, 403)

    def test_cross_site_cors_get_blocked(self):
        # cross-site fetch() GET (Mode=cors) blocked even though GET is safe
        factory = RequestFactory()
        request = factory.get('/test/', HTTP_SEC_FETCH_SITE='cross-site', HTTP_SEC_FETCH_MODE='cors')
        mw = _make_middleware()
        result = mw.process_view(request, _dummy_view, (), {})
        self.assertIsNotNone(result)
        self.assertEqual(result.status_code, 403)

    def test_same_site_non_navigation_get_blocked(self):
        # same-site fetch() from subdomain blocked under DEFAULT
        factory = RequestFactory()
        request = factory.get('/test/', HTTP_SEC_FETCH_SITE='same-site', HTTP_SEC_FETCH_MODE='cors')
        mw = _make_middleware()
        result = mw.process_view(request, _dummy_view, (), {})
        self.assertIsNotNone(result)
        self.assertEqual(result.status_code, 403)

    def test_cross_site_object_dest_blocked(self):
        # cross-site <object> embed: Mode=navigate + Dest=object blocked per web.dev spec
        factory = RequestFactory()
        request = factory.get(
            '/test/',
            HTTP_SEC_FETCH_SITE='cross-site',
            HTTP_SEC_FETCH_MODE='navigate',
            HTTP_SEC_FETCH_DEST='object',
        )
        mw = _make_middleware()
        result = mw.process_view(request, _dummy_view, (), {})
        self.assertIsNotNone(result)
        self.assertEqual(result.status_code, 403)

    def test_cross_site_embed_dest_blocked(self):
        # cross-site <embed> tag: Mode=navigate + Dest=embed blocked per web.dev spec
        factory = RequestFactory()
        request = factory.get(
            '/test/',
            HTTP_SEC_FETCH_SITE='cross-site',
            HTTP_SEC_FETCH_MODE='navigate',
            HTTP_SEC_FETCH_DEST='embed',
        )
        mw = _make_middleware()
        result = mw.process_view(request, _dummy_view, (), {})
        self.assertIsNotNone(result)
        self.assertEqual(result.status_code, 403)

    def test_cross_site_document_dest_allowed(self):
        # cross-site link click: Mode=navigate + Dest=document allowed (normal navigation)
        factory = RequestFactory()
        request = factory.get(
            '/test/',
            HTTP_SEC_FETCH_SITE='cross-site',
            HTTP_SEC_FETCH_MODE='navigate',
            HTTP_SEC_FETCH_DEST='document',
        )
        mw = _make_middleware()
        result = mw.process_view(request, _dummy_view, (), {})
        self.assertIsNone(result)
        self.assertTrue(request._fetch_metadata['allowed'])

    def test_nested_navigate_blocked(self):
        # cross-site iframe: Mode=nested-navigate blocked (deliberate choice)
        factory = RequestFactory()
        request = factory.get(
            '/test/',
            HTTP_SEC_FETCH_SITE='cross-site',
            HTTP_SEC_FETCH_MODE='nested-navigate',
            HTTP_SEC_FETCH_DEST='iframe',
        )
        mw = _make_middleware()
        result = mw.process_view(request, _dummy_view, (), {})
        self.assertIsNotNone(result)
        self.assertEqual(result.status_code, 403)


class TestSafeMethodExemption(SimpleTestCase):
    """ALLOW_SAFE_METHODS passes all GET/HEAD regardless of site."""

    @override_settings(FETCH_METADATA_PRESET='LAX')
    def test_cross_site_cors_get_allowed(self):
        # cross-site fetch() GET passes under LAX
        factory = RequestFactory()
        request = factory.get('/test/', HTTP_SEC_FETCH_SITE='cross-site', HTTP_SEC_FETCH_MODE='cors')
        mw = _make_middleware()
        result = mw.process_view(request, _dummy_view, (), {})
        self.assertIsNone(result)
        self.assertTrue(request._fetch_metadata['allowed'])
        self.assertEqual(request._fetch_metadata['reason'], 'safe_method')

    @override_settings(FETCH_METADATA_PRESET='LAX')
    def test_cross_site_no_cors_get_allowed(self):
        # cross-site <script>/<img> GET passes under LAX
        factory = RequestFactory()
        request = factory.get('/test/', HTTP_SEC_FETCH_SITE='cross-site', HTTP_SEC_FETCH_MODE='no-cors')
        mw = _make_middleware()
        result = mw.process_view(request, _dummy_view, (), {})
        self.assertIsNone(result)
        self.assertTrue(request._fetch_metadata['allowed'])

    @override_settings(FETCH_METADATA_PRESET='LAX')
    def test_cross_site_nested_navigate_get_allowed(self):
        # cross-site iframe GET passes under LAX
        factory = RequestFactory()
        request = factory.get('/test/', HTTP_SEC_FETCH_SITE='cross-site', HTTP_SEC_FETCH_MODE='nested-navigate')
        mw = _make_middleware()
        result = mw.process_view(request, _dummy_view, (), {})
        self.assertIsNone(result)
        self.assertTrue(request._fetch_metadata['allowed'])

    @override_settings(FETCH_METADATA_PRESET='LAX')
    def test_cross_site_head_allowed(self):
        # cross-site HEAD passes under LAX
        factory = RequestFactory()
        request = factory.head('/test/', HTTP_SEC_FETCH_SITE='cross-site', HTTP_SEC_FETCH_MODE='cors')
        mw = _make_middleware()
        result = mw.process_view(request, _dummy_view, (), {})
        self.assertIsNone(result)
        self.assertTrue(request._fetch_metadata['allowed'])

    @override_settings(FETCH_METADATA_PRESET='LAX')
    def test_cross_site_post_still_blocked(self):
        # cross-site POST blocked even under LAX
        factory = RequestFactory()
        request = factory.post('/test/', HTTP_SEC_FETCH_SITE='cross-site', HTTP_SEC_FETCH_MODE='cors')
        mw = _make_middleware()
        result = mw.process_view(request, _dummy_view, (), {})
        self.assertIsNotNone(result)
        self.assertEqual(result.status_code, 403)

    def test_cross_site_get_blocked_under_default(self):
        # cross-site fetch() GET still blocked under DEFAULT
        factory = RequestFactory()
        request = factory.get('/test/', HTTP_SEC_FETCH_SITE='cross-site', HTTP_SEC_FETCH_MODE='cors')
        mw = _make_middleware()
        result = mw.process_view(request, _dummy_view, (), {})
        self.assertIsNotNone(result)
        self.assertEqual(result.status_code, 403)

    @override_settings(FETCH_METADATA_ALLOW_SAFE_METHODS=True)
    def test_explicit_setting_overrides_preset(self):
        # explicit ALLOW_SAFE_METHODS=True overrides DEFAULT preset
        factory = RequestFactory()
        request = factory.get('/test/', HTTP_SEC_FETCH_SITE='cross-site', HTTP_SEC_FETCH_MODE='cors')
        mw = _make_middleware()
        result = mw.process_view(request, _dummy_view, (), {})
        self.assertIsNone(result)
        self.assertTrue(request._fetch_metadata['allowed'])


class TestReportOnly(SimpleTestCase):
    """Report-only mode logs but does not block."""

    @override_settings(FETCH_METADATA_REPORT_ONLY=True)
    def test_report_only_logs_but_passes(self):
        factory = RequestFactory()
        request = factory.post('/test/', HTTP_SEC_FETCH_SITE='cross-site', HTTP_SEC_FETCH_MODE='cors')
        mw = _make_middleware()
        with self.assertLogs('fetch_metadata', level='WARNING') as cm:
            result = mw.process_view(request, _dummy_view, (), {})
        self.assertIsNone(result)
        self.assertTrue(request._fetch_metadata['report_only'])
        self.assertIn('cross-site', cm.output[0])

    @override_settings(FETCH_METADATA_REPORT_ONLY=True)
    def test_report_only_still_annotates(self):
        factory = RequestFactory()
        request = factory.post('/test/', HTTP_SEC_FETCH_SITE='cross-site', HTTP_SEC_FETCH_MODE='cors')
        mw = _make_middleware()
        with self.assertLogs('fetch_metadata', level='WARNING'):
            mw.process_view(request, _dummy_view, (), {})
        self.assertFalse(request._fetch_metadata['allowed'])
        self.assertEqual(request._fetch_metadata['reason'], 'blocked')


class TestExemptPaths(SimpleTestCase):
    """EXEMPT_PATHS bypasses all checks for matching path prefixes."""

    @override_settings(FETCH_METADATA_EXEMPT_PATHS=['/.well-known/', '/api/'])
    def test_exempt_path_passes(self):
        factory = RequestFactory()
        request = factory.post('/.well-known/openid-configuration', HTTP_SEC_FETCH_SITE='cross-site')
        mw = _make_middleware()
        result = mw.process_view(request, _dummy_view, (), {})
        self.assertIsNone(result)
        self.assertEqual(request._fetch_metadata['reason'], 'exempt_path')

    @override_settings(FETCH_METADATA_EXEMPT_PATHS=['/api/'])
    def test_non_matching_path_still_checked(self):
        factory = RequestFactory()
        request = factory.post('/test/', HTTP_SEC_FETCH_SITE='cross-site', HTTP_SEC_FETCH_MODE='cors')
        mw = _make_middleware()
        result = mw.process_view(request, _dummy_view, (), {})
        self.assertIsNotNone(result)
        self.assertEqual(result.status_code, 403)


class TestDecoratorExemption(SimpleTestCase):
    """@fetch_metadata_exempt view bypasses all checks."""

    def test_exempt_view_passes_cross_site(self):
        factory = RequestFactory()
        request = factory.post('/test/', HTTP_SEC_FETCH_SITE='cross-site', HTTP_SEC_FETCH_MODE='cors')
        mw = _make_middleware()
        result = mw.process_view(request, _exempt_view, (), {})
        self.assertIsNone(result)
        self.assertEqual(request._fetch_metadata['reason'], 'exempt')


class TestPolicyDecorator(SimpleTestCase):
    """@fetch_metadata_policy overrides global config for a specific view."""

    def test_view_policy_allows_same_site(self):
        # _policy_view allows same-site, which DEFAULT would block
        factory = RequestFactory()
        request = factory.post('/test/', HTTP_SEC_FETCH_SITE='same-site', HTTP_SEC_FETCH_MODE='cors')
        mw = _make_middleware()
        result = mw.process_view(request, _policy_view, (), {})
        self.assertIsNone(result)
        self.assertTrue(request._fetch_metadata['allowed'])

    def test_view_policy_still_blocks_cross_site(self):
        # _policy_view allows same-origin + same-site, but not cross-site
        factory = RequestFactory()
        request = factory.post('/test/', HTTP_SEC_FETCH_SITE='cross-site', HTTP_SEC_FETCH_MODE='cors')
        mw = _make_middleware()
        result = mw.process_view(request, _policy_view, (), {})
        self.assertIsNotNone(result)
        self.assertEqual(result.status_code, 403)

    def test_view_policy_disables_navigations(self):
        # per-view ALLOW_NAVIGATIONS=False overrides DEFAULT's True
        def view(request):
            pass

        view.fetch_metadata_policy = {'ALLOW_NAVIGATIONS': False}
        factory = RequestFactory()
        request = factory.get('/test/', HTTP_SEC_FETCH_SITE='cross-site', HTTP_SEC_FETCH_MODE='navigate')
        mw = _make_middleware()
        result = mw.process_view(request, view, (), {})
        self.assertIsNotNone(result)
        self.assertEqual(result.status_code, 403)

    def test_view_policy_fail_open_override(self):
        # per-view FAIL_OPEN=False blocks missing header even under DEFAULT
        def view(request):
            pass

        view.fetch_metadata_policy = {'FAIL_OPEN': False}
        factory = RequestFactory()
        request = factory.post('/test/')
        mw = _make_middleware()
        result = mw.process_view(request, view, (), {})
        self.assertIsNotNone(result)
        self.assertEqual(result.status_code, 403)


class TestViolationLogging(SimpleTestCase):
    """Violations log all 4 Sec-Fetch-* headers."""

    def test_violation_logs_all_headers(self):
        factory = RequestFactory()
        request = factory.post(
            '/test/',
            HTTP_SEC_FETCH_SITE='cross-site',
            HTTP_SEC_FETCH_MODE='cors',
            HTTP_SEC_FETCH_DEST='empty',
            HTTP_SEC_FETCH_USER='?1',
        )
        mw = _make_middleware()
        with self.assertLogs('fetch_metadata', level='WARNING') as cm:
            mw.process_view(request, _dummy_view, (), {})
        log_msg = cm.output[0]
        self.assertIn('cross-site', log_msg)
        self.assertIn('cors', log_msg)
        self.assertIn('empty', log_msg)
        self.assertIn('?1', log_msg)


class TestAllMethodsChecked(SimpleTestCase):
    """All HTTP methods are checked (not just POST)."""

    def test_put_blocked(self):
        factory = RequestFactory()
        request = factory.put('/test/', HTTP_SEC_FETCH_SITE='cross-site', HTTP_SEC_FETCH_MODE='cors')
        mw = _make_middleware()
        result = mw.process_view(request, _dummy_view, (), {})
        self.assertIsNotNone(result)
        self.assertEqual(result.status_code, 403)

    def test_delete_blocked(self):
        factory = RequestFactory()
        request = factory.delete('/test/', HTTP_SEC_FETCH_SITE='cross-site', HTTP_SEC_FETCH_MODE='cors')
        mw = _make_middleware()
        result = mw.process_view(request, _dummy_view, (), {})
        self.assertIsNotNone(result)
        self.assertEqual(result.status_code, 403)

    def test_patch_blocked(self):
        factory = RequestFactory()
        request = factory.patch('/test/', HTTP_SEC_FETCH_SITE='cross-site', HTTP_SEC_FETCH_MODE='cors')
        mw = _make_middleware()
        result = mw.process_view(request, _dummy_view, (), {})
        self.assertIsNotNone(result)
        self.assertEqual(result.status_code, 403)

    def test_get_blocked_when_cross_site_cors(self):
        # GET with cross-site + cors = blocked (RIP behavior)
        factory = RequestFactory()
        request = factory.get('/test/', HTTP_SEC_FETCH_SITE='cross-site', HTTP_SEC_FETCH_MODE='cors')
        mw = _make_middleware()
        result = mw.process_view(request, _dummy_view, (), {})
        self.assertIsNotNone(result)
        self.assertEqual(result.status_code, 403)


class TestAnnotation(SimpleTestCase):
    """request._fetch_metadata is set on every request."""

    def test_allowed_request_annotated(self):
        factory = RequestFactory()
        request = factory.post('/test/', HTTP_SEC_FETCH_SITE='same-origin', HTTP_SEC_FETCH_MODE='cors')
        mw = _make_middleware()
        mw.process_view(request, _dummy_view, (), {})
        self.assertTrue(hasattr(request, '_fetch_metadata'))
        self.assertTrue(request._fetch_metadata['allowed'])

    def test_blocked_request_annotated(self):
        factory = RequestFactory()
        request = factory.post('/test/', HTTP_SEC_FETCH_SITE='cross-site', HTTP_SEC_FETCH_MODE='cors')
        mw = _make_middleware()
        mw.process_view(request, _dummy_view, (), {})
        self.assertTrue(hasattr(request, '_fetch_metadata'))
        self.assertFalse(request._fetch_metadata['allowed'])


class TestEvaluateResult(SimpleTestCase):
    """_evaluate() returns the expected structure."""

    def test_result_structure(self):
        factory = RequestFactory()
        request = factory.post('/test/', HTTP_SEC_FETCH_SITE='same-origin', HTTP_SEC_FETCH_MODE='cors')
        mw = _make_middleware()
        result = mw._evaluate(request, _dummy_view)
        self.assertIn('allowed', result)
        self.assertIn('reason', result)
        self.assertIn('policy', result)
        self.assertIn('headers', result)
        self.assertIsInstance(result['headers'], dict)
        self.assertIn('site', result['headers'])
        self.assertIn('mode', result['headers'])
        self.assertIn('dest', result['headers'])
        self.assertIn('user', result['headers'])
