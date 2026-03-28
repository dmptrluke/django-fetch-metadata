from debug_toolbar.panels import Panel


class FetchMetadataPanel(Panel):
    """Django Debug Toolbar panel showing Fetch Metadata header info."""

    title = 'Fetch Metadata'
    template = 'fetch_metadata/panels/fetch_metadata.html'

    @property
    def nav_subtitle(self):
        stats = self.get_stats()
        if not stats.get('has_data'):
            return ''
        decision = stats.get('reason', '')
        site = stats.get('site', '')
        return f'{site} ({decision})' if site else decision

    def generate_stats(self, request, response):
        data = getattr(request, '_fetch_metadata', None)
        if data is None:
            self.record_stats({'has_data': False})
            return

        headers = data.get('headers', {})
        self.record_stats(
            {
                'has_data': True,
                'site': headers.get('site', '') or 'not sent',
                'mode': headers.get('mode', '') or 'not sent',
                'dest': headers.get('dest', '') or 'not sent',
                'user': headers.get('user', '') or 'not sent',
                'allowed': data.get('allowed', False),
                'reason': data.get('reason', ''),
                'report_only': data.get('report_only', False),
                'policy': data.get('policy', {}),
            }
        )
