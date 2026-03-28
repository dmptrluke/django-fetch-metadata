# Configuration

All settings are optional. The DEFAULT preset works without any configuration.

## Settings Reference

| Setting | Default | Description |
|---------|---------|-------------|
| `FETCH_METADATA_PRESET` | `'DEFAULT'` | Named preset. Provides defaults for all other settings. |
| `FETCH_METADATA_ALLOWED_SITES` | preset | `Sec-Fetch-Site` values that pass. List of strings. |
| `FETCH_METADATA_ALLOW_NAVIGATIONS` | preset | Allow cross-site `navigate` requests with safe methods (GET/HEAD). |
| `FETCH_METADATA_FAIL_OPEN` | preset | Pass requests that don't include a `Sec-Fetch-Site` header. |
| `FETCH_METADATA_REPORT_ONLY` | `False` | Log violations but don't block. Global only (not per-view). |
| `FETCH_METADATA_EXEMPT_PATHS` | `[]` | Path prefixes that skip all checks. Global only. |
| `FETCH_METADATA_FAILURE_VIEW` | `None` | Dotted path to a custom 403 view callable. |

Explicit settings override the active preset. For example, setting
`FETCH_METADATA_PRESET = 'API'` and `FETCH_METADATA_FAIL_OPEN = False`
uses the API preset but overrides its fail-open behavior.

## Preset Resolution

Settings are resolved per-request in this order:

```
@fetch_metadata_policy on view  >  FETCH_METADATA_{name} setting  >  preset default
```

Per-view decorators can only override policy settings (`ALLOWED_SITES`,
`ALLOW_NAVIGATIONS`, `FAIL_OPEN`). Deployment settings (`REPORT_ONLY`,
`EXEMPT_PATHS`) are always global.

## Exempt Paths

`FETCH_METADATA_EXEMPT_PATHS` takes a list of path prefixes. Any request
whose path starts with a listed prefix skips all checks.

```python
FETCH_METADATA_EXEMPT_PATHS = [
    '/.well-known/',     # OIDC discovery, JWKS
    '/webhooks/',        # external webhook receivers
    '/api/public/',      # unauthenticated public API
]
```

Path matching is prefix-based. `'/api/'` matches `/api/v1/users`,
`/api/health`, etc.

## Custom Failure View

By default, blocked requests get a plain `403 Forbidden` response. With
`DEBUG=True`, a debug page shows the request headers, active policy, and
rejection reason.

To use a custom view in production:

```python
FETCH_METADATA_FAILURE_VIEW = 'myapp.views.fetch_metadata_denied'
```

The view receives:

```python
def fetch_metadata_denied(request, reason=None, headers=None):
    # reason: string like 'blocked', 'no_header_strict'
    # headers: dict with 'site', 'mode', 'dest', 'user' keys
    return HttpResponseForbidden('...')
```

If your custom view raises an exception, the middleware falls back to the
default 403 and logs the error.

## Logging

All violations are logged to the `fetch_metadata` logger at WARNING level,
including in report-only mode. The log message includes all four Sec-Fetch-*
header values, the request method, path, and rejection reason.

```python
LOGGING = {
    'loggers': {
        'fetch_metadata': {
            'handlers': ['console'],
            'level': 'WARNING',
        },
    },
}
```

## System Checks

Add `'fetch_metadata'` to `INSTALLED_APPS` to enable system checks:

| ID | Level | Condition |
|----|-------|-----------|
| `fetch_metadata.W001` | Warning | Middleware not in `MIDDLEWARE` |
| `fetch_metadata.W002` | Warning | `REPORT_ONLY=True` with `DEBUG=False` |
| `fetch_metadata.E001` | Error | Invalid `FETCH_METADATA_PRESET` value |
| `fetch_metadata.E002` | Error | `FETCH_METADATA_ALLOWED_SITES` is a string (should be list) |
| `fetch_metadata.E003` | Error | `FETCH_METADATA_FAILURE_VIEW` not importable |

Adding to `INSTALLED_APPS` is optional. The middleware works without it.
