from django.conf import settings

from fetch_metadata.presets import PRESETS

_SENTINEL = object()


def get_config(name):
    """Read a FETCH_METADATA_* setting, falling back to the active preset."""
    val = getattr(settings, f'FETCH_METADATA_{name}', _SENTINEL)
    if val is not _SENTINEL:
        return val
    preset_name = getattr(settings, 'FETCH_METADATA_PRESET', 'DEFAULT')
    return PRESETS[preset_name][name]
