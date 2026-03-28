from django.apps import AppConfig
from django.core.checks import Tags, register


class FetchMetadataConfig(AppConfig):
    name = 'fetch_metadata'
    verbose_name = 'Django Fetch Metadata'

    def ready(self):
        from fetch_metadata.systemchecks import check_settings

        register(Tags.security)(check_settings)
