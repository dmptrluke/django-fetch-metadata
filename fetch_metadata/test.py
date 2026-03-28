SEC_FETCH_HEADER_MAP = {
    'site': 'HTTP_SEC_FETCH_SITE',
    'mode': 'HTTP_SEC_FETCH_MODE',
    'dest': 'HTTP_SEC_FETCH_DEST',
    'user': 'HTTP_SEC_FETCH_USER',
}


class FetchMetadataTestMixin:
    """Mixin for testing views against Fetch Metadata policies.

    Add to a Django TestCase alongside your test client. Each method makes
    a request with the specified Sec-Fetch-* headers and asserts the outcome.
    """

    def _make_fetch_request(self, url, method='POST', site='same-origin', mode='cors', dest='', user='', **kwargs):
        """Build and send a request with Sec-Fetch-* headers."""
        headers = {}
        if site is not None:
            headers['HTTP_SEC_FETCH_SITE'] = site
        if mode is not None:
            headers['HTTP_SEC_FETCH_MODE'] = mode
        if dest is not None:
            headers['HTTP_SEC_FETCH_DEST'] = dest
        if user is not None and user != '':
            headers['HTTP_SEC_FETCH_USER'] = user

        client_method = getattr(self.client, method.lower())
        return client_method(url, **headers, **kwargs)

    def assert_allows(self, url, method='POST', site='same-origin', mode='cors', **kwargs):
        """Assert the request is not blocked (status != 403)."""
        response = self._make_fetch_request(url, method=method, site=site, mode=mode, **kwargs)
        assert response.status_code != 403, (
            f'Expected request to be allowed, but got 403. method={method} site={site} mode={mode} url={url}'
        )
        return response

    def assert_blocks(self, url, method='POST', site='cross-site', mode='cors', **kwargs):
        """Assert the request returns 403."""
        response = self._make_fetch_request(url, method=method, site=site, mode=mode, **kwargs)
        assert response.status_code == 403, (
            f'Expected request to be blocked (403), but got {response.status_code}. '
            f'method={method} site={site} mode={mode} url={url}'
        )
        return response
