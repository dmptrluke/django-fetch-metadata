import inspect
from functools import wraps

from django.utils.decorators import classonlymethod


def _patch_as_view(cls, attr, value):
    """Wrap as_view to propagate a fetch metadata attribute to the view function."""
    original = cls.as_view.__func__

    def as_view(cls, **initkwargs):
        view = original(cls, **initkwargs)
        setattr(view, attr, value)
        return view

    cls.as_view = classonlymethod(as_view)
    return cls


def _wrap_view_func(view, attr, value):
    """Wrap a view function and stamp a fetch metadata attribute on the wrapper.

    Handles both sync and async views. The attribute is set after @wraps
    so __dict__.update() cannot overwrite it.
    """
    if inspect.iscoroutinefunction(view):

        @wraps(view)
        async def _wrapped(request, *args, **kwargs):
            return await view(request, *args, **kwargs)
    else:

        @wraps(view)
        def _wrapped(request, *args, **kwargs):
            return view(request, *args, **kwargs)

    setattr(_wrapped, attr, value)
    return _wrapped


def fetch_metadata_exempt(view):
    """Mark a view as exempt from Fetch Metadata checks."""
    if inspect.isclass(view):
        return _patch_as_view(view, 'fetch_metadata_exempt', True)
    return _wrap_view_func(view, 'fetch_metadata_exempt', True)


def fetch_metadata_policy(allowed_sites=None, allow_navigations=None, allow_safe_methods=None, fail_open=None):
    """Override the global Fetch Metadata policy for a specific view.

    Only the parameters you pass are overridden; the rest fall through
    to the global config. Deployment settings (REPORT_ONLY, EXEMPT_PATHS)
    cannot be overridden per-view.
    """
    policy = {
        k: v
        for k, v in {
            'ALLOWED_SITES': allowed_sites,
            'ALLOW_NAVIGATIONS': allow_navigations,
            'ALLOW_SAFE_METHODS': allow_safe_methods,
            'FAIL_OPEN': fail_open,
        }.items()
        if v is not None
    }

    def decorator(view):
        if inspect.isclass(view):
            return _patch_as_view(view, 'fetch_metadata_policy', policy)
        return _wrap_view_func(view, 'fetch_metadata_policy', policy)

    return decorator
