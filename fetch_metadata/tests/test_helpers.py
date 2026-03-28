from django.test import SimpleTestCase

from fetch_metadata.test import FetchMetadataTestMixin


class TestFetchMetadataTestMixin(FetchMetadataTestMixin, SimpleTestCase):
    def test_assert_allows_passes_for_allowed_request(self):
        # same-origin POST is allowed under DEFAULT
        response = self.assert_allows('/test/', method='POST', site='same-origin')
        self.assertEqual(response.status_code, 200)

    def test_assert_allows_fails_for_blocked_request(self):
        # cross-site POST should be blocked, so assert_allows raises
        with self.assertRaises(AssertionError):
            self.assert_allows('/test/', method='POST', site='cross-site')

    def test_assert_blocks_passes_for_blocked_request(self):
        # cross-site POST returns 403
        response = self.assert_blocks('/test/', method='POST', site='cross-site')
        self.assertEqual(response.status_code, 403)

    def test_assert_blocks_fails_for_allowed_request(self):
        # same-origin POST is allowed, so assert_blocks raises
        with self.assertRaises(AssertionError):
            self.assert_blocks('/test/', method='POST', site='same-origin')

    def test_custom_method_forwarded(self):
        # PUT method forwarded correctly
        response = self.assert_blocks('/test/', method='PUT', site='cross-site')
        self.assertEqual(response.status_code, 403)

    def test_get_navigation_allowed(self):
        # cross-site navigate GET is allowed under DEFAULT
        response = self.assert_allows('/test/', method='GET', site='cross-site', mode='navigate')
        self.assertEqual(response.status_code, 200)
