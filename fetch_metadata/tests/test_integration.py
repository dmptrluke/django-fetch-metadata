from django.test import SimpleTestCase, override_settings


class TestIntegration(SimpleTestCase):
    """Full-stack tests using Django test Client through middleware."""

    def test_cross_site_post_blocked(self):
        # cross-site POST returns 403 through full middleware stack
        response = self.client.post('/test/', HTTP_SEC_FETCH_SITE='cross-site', HTTP_SEC_FETCH_MODE='cors')
        self.assertEqual(response.status_code, 403)

    def test_same_origin_post_allowed(self):
        # same-origin POST passes through
        response = self.client.post('/test/', HTTP_SEC_FETCH_SITE='same-origin', HTTP_SEC_FETCH_MODE='cors')
        self.assertEqual(response.status_code, 200)

    def test_exempt_view_passes_cross_site(self):
        # @fetch_metadata_exempt view allows cross-site POST
        response = self.client.post('/exempt/', HTTP_SEC_FETCH_SITE='cross-site', HTTP_SEC_FETCH_MODE='cors')
        self.assertEqual(response.status_code, 200)

    def test_cross_site_navigate_get_allowed(self):
        # cross-site link click allowed under DEFAULT
        response = self.client.get('/test/', HTTP_SEC_FETCH_SITE='cross-site', HTTP_SEC_FETCH_MODE='navigate')
        self.assertEqual(response.status_code, 200)

    def test_options_passes(self):
        # OPTIONS always passes (CORS preflight)
        response = self.client.options('/test/', HTTP_SEC_FETCH_SITE='cross-site', HTTP_SEC_FETCH_MODE='cors')
        self.assertEqual(response.status_code, 200)

    def test_cbv_exempt_passes(self):
        # @fetch_metadata_exempt on CBV allows cross-site POST
        response = self.client.post('/cbv-exempt/', HTTP_SEC_FETCH_SITE='cross-site', HTTP_SEC_FETCH_MODE='cors')
        self.assertEqual(response.status_code, 200)

    def test_cbv_policy_allows_cross_site(self):
        # @fetch_metadata_policy on CBV allows cross-site when configured
        response = self.client.post('/cbv-policy/', HTTP_SEC_FETCH_SITE='cross-site', HTTP_SEC_FETCH_MODE='cors')
        self.assertEqual(response.status_code, 200)

    def test_custom_policy_allows_same_site(self):
        # view with policy allowing same-site
        response = self.client.post('/custom-policy/', HTTP_SEC_FETCH_SITE='same-site', HTTP_SEC_FETCH_MODE='cors')
        self.assertEqual(response.status_code, 200)

    def test_strict_policy_blocks_missing_header(self):
        # view with strict policy (fail_open=False) blocks missing header
        response = self.client.post('/strict-policy/')
        self.assertEqual(response.status_code, 403)

    @override_settings(FETCH_METADATA_REPORT_ONLY=True)
    def test_report_only_passes_violation(self):
        # report-only mode: violation logged but request passes
        response = self.client.post('/test/', HTTP_SEC_FETCH_SITE='cross-site', HTTP_SEC_FETCH_MODE='cors')
        self.assertEqual(response.status_code, 200)

    def test_vary_header_on_allowed_response(self):
        # Vary header includes Sec-Fetch-* headers to prevent cache poisoning
        response = self.client.post('/test/', HTTP_SEC_FETCH_SITE='same-origin', HTTP_SEC_FETCH_MODE='cors')
        vary = response.get('Vary', '')
        self.assertIn('Sec-Fetch-Site', vary)
        self.assertIn('Sec-Fetch-Mode', vary)
        self.assertIn('Sec-Fetch-Dest', vary)

    def test_vary_header_on_blocked_response(self):
        # Vary header also present on 403 responses
        response = self.client.post('/test/', HTTP_SEC_FETCH_SITE='cross-site', HTTP_SEC_FETCH_MODE='cors')
        vary = response.get('Vary', '')
        self.assertIn('Sec-Fetch-Site', vary)

    def test_cross_site_object_blocked(self):
        # cross-site <object> embed blocked through full stack
        response = self.client.get(
            '/test/',
            HTTP_SEC_FETCH_SITE='cross-site',
            HTTP_SEC_FETCH_MODE='navigate',
            HTTP_SEC_FETCH_DEST='object',
        )
        self.assertEqual(response.status_code, 403)

    @override_settings(FETCH_METADATA_PRESET='LAX')
    def test_lax_allows_cross_site_get(self):
        # LAX preset allows cross-site fetch() GET through full stack
        response = self.client.get('/test/', HTTP_SEC_FETCH_SITE='cross-site', HTTP_SEC_FETCH_MODE='cors')
        self.assertEqual(response.status_code, 200)

    @override_settings(FETCH_METADATA_PRESET='LAX')
    def test_lax_blocks_cross_site_post(self):
        # LAX preset still blocks cross-site POST
        response = self.client.post('/test/', HTTP_SEC_FETCH_SITE='cross-site', HTTP_SEC_FETCH_MODE='cors')
        self.assertEqual(response.status_code, 403)
