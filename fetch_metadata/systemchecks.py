from django.conf import settings
from django.core.checks import Error
from django.core.checks import Warning as CheckWarning

from fetch_metadata.presets import PRESETS


def check_settings(**kwargs):
    """Validate Fetch Metadata configuration at startup."""
    errors = []

    # W001: middleware not in MIDDLEWARE
    middleware = getattr(settings, 'MIDDLEWARE', [])
    if 'fetch_metadata.middleware.FetchMetadataMiddleware' not in middleware:
        errors.append(
            CheckWarning(
                'FetchMetadataMiddleware is not in your MIDDLEWARE setting.',
                hint="Add 'fetch_metadata.middleware.FetchMetadataMiddleware' to MIDDLEWARE.",
                id='fetch_metadata.W001',
            )
        )

    # E001: invalid preset
    preset = getattr(settings, 'FETCH_METADATA_PRESET', None)
    if preset is not None and preset not in PRESETS:
        errors.append(
            Error(
                f'FETCH_METADATA_PRESET is {preset!r}, which is not a valid preset. '
                f'Choose from: {", ".join(sorted(PRESETS.keys()))}',
                id='fetch_metadata.E001',
            )
        )
        # return early: W002 and other checks depend on valid preset resolution
        return errors

    # W002: report-only in non-debug (production without enforcement)
    from fetch_metadata.conf import get_config

    if get_config('REPORT_ONLY') and not settings.DEBUG:
        errors.append(
            CheckWarning(
                'FETCH_METADATA_REPORT_ONLY is True with DEBUG=False. '
                'Fetch Metadata violations will be logged but not blocked.',
                id='fetch_metadata.W002',
            )
        )

    # E002: ALLOWED_SITES is a string, not a list/tuple
    allowed_sites = getattr(settings, 'FETCH_METADATA_ALLOWED_SITES', None)
    if allowed_sites is not None and isinstance(allowed_sites, str):
        errors.append(
            Error(
                f'FETCH_METADATA_ALLOWED_SITES should be a list or tuple, not a string. Got: {allowed_sites!r}',
                id='fetch_metadata.E002',
            )
        )

    # E003: failure view not importable
    failure_view = getattr(settings, 'FETCH_METADATA_FAILURE_VIEW', None)
    if failure_view is not None:
        from django.urls import get_callable

        try:
            get_callable(failure_view)
        except (ImportError, AttributeError, ValueError):
            errors.append(
                Error(
                    f'FETCH_METADATA_FAILURE_VIEW {failure_view!r} could not be imported.',
                    id='fetch_metadata.E003',
                )
            )

    return errors
