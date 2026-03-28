# django-fetch-metadata

Resource isolation policy for Django using
[Fetch Metadata](https://web.dev/articles/fetch-metadata) request headers.

Browsers send `Sec-Fetch-Site` and `Sec-Fetch-Mode` headers on every request,
indicating where the request came from and how it was initiated. This middleware
uses those headers to block cross-site attacks while allowing legitimate
same-origin requests and direct navigations.

This is a defense-in-depth layer that works alongside Django's CSRF middleware,
not a replacement for it. Non-browser clients that don't send Fetch Metadata
headers (curl, API consumers, webhooks) pass through by default.

## Installation

```bash
pip install django-fetch-metadata
```

Add the middleware to your `MIDDLEWARE` setting, before `CsrfViewMiddleware`:

```python
MIDDLEWARE = [
    'django.middleware.common.CommonMiddleware',
    'fetch_metadata.middleware.FetchMetadataMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    # ...
]
```

The DEFAULT preset is opinionated: it blocks all cross-site requests except
link clicks (navigations). This includes cross-site `fetch()` GETs, `<script>`
includes, `<img>` loads, and iframe embeds. For CSRF-like protection that only
blocks cross-site state-changing requests, use the `LAX` preset:

```python
FETCH_METADATA_PRESET = 'LAX'
```

To enable system checks, add `'fetch_metadata'` to `INSTALLED_APPS`.

## Presets

Four named presets cover common configurations:

| Preset | Blocks cross-site GETs | Blocks navigations | Fail Open | Use Case |
|--------|----------------------|-------------------|-----------|----------|
| **DEFAULT** | Yes | Link clicks allowed | Yes | Full resource isolation |
| **LAX** | No | No | Yes | CSRF-like protection |
| **API** | Yes | Yes | Yes | API endpoints |
| **STRICT** | Yes | Yes | No | Admin panels, internal tools |

```python
FETCH_METADATA_PRESET = 'API'
```

Any settings you specify explicitly will override the preset values.

See [Presets](docs/presets.md) for detailed scenarios.

## Configuration

All settings are optional. The `DEFAULT` preset works without any configuration.

| Setting | Default | Description |
|---------|---------|-------------|
| `FETCH_METADATA_PRESET` | `'DEFAULT'` | Named preset: `DEFAULT`, `LAX`, `API`, or `STRICT` |
| `FETCH_METADATA_ALLOWED_SITES` | preset | List of allowed `Sec-Fetch-Site` values |
| `FETCH_METADATA_ALLOW_NAVIGATIONS` | preset | Allow cross-site `navigate` + GET/HEAD |
| `FETCH_METADATA_ALLOW_SAFE_METHODS` | preset | Allow all cross-site GET/HEAD requests |
| `FETCH_METADATA_FAIL_OPEN` | preset | Pass requests with no `Sec-Fetch-Site` header |
| `FETCH_METADATA_REPORT_ONLY` | `False` | Log violations without blocking |
| `FETCH_METADATA_EXEMPT_PATHS` | `[]` | Path prefixes to skip (e.g. `['/.well-known/']`) |
| `FETCH_METADATA_FAILURE_VIEW` | `None` | Dotted path to a custom 403 view |

See [Configuration](docs/configuration.md) for details.

## Per-View Decorators

Exempt a view from all checks:

```python
from fetch_metadata.decorators import fetch_metadata_exempt

@fetch_metadata_exempt
class WebhookView(View):
    ...
```

Override the policy for a specific view:

```python
from fetch_metadata.decorators import fetch_metadata_policy

@fetch_metadata_policy(allowed_sites=['same-origin', 'same-site', 'none'])
class SubdomainAPIView(View):
    ...
```

Both decorators work on function-based views too:

```python
@fetch_metadata_exempt
def webhook_receiver(request):
    ...
```

## Test Utilities

`FetchMetadataTestMixin` provides assertion helpers for testing views against
the policy:

```python
from django.test import TestCase
from fetch_metadata.test import FetchMetadataTestMixin

class MyViewTests(FetchMetadataTestMixin, TestCase):
    def test_cross_site_blocked(self):
        self.assert_blocks('/api/data/')

    def test_same_origin_allowed(self):
        self.assert_allows('/api/data/')
```

`assert_blocks` sends a cross-site POST by default. `assert_allows` sends a
same-origin POST. Both accept `method`, `site`, and `mode` keyword arguments.

## How It Works

The middleware runs on every request via Django's `process_view` hook:

1. **OPTIONS** requests always pass (CORS preflight carries no credentials)
2. Exempt views and paths skip all checks
3. The active policy is resolved (per-view decorator, or global preset + overrides)
4. Missing `Sec-Fetch-Site` header: pass if `FAIL_OPEN`, block if not
5. Header value in `allowed_sites`: pass
6. GET/HEAD with `ALLOW_SAFE_METHODS`: pass
7. Cross-site navigation via GET/HEAD with `ALLOW_NAVIGATIONS`: pass
8. Everything else: log at WARNING and block (or pass in report-only mode)

Under DEFAULT, all cross-site requests are checked, including GETs. A cross-site
`fetch()` GET is blocked. A cross-site link click (`Sec-Fetch-Mode: navigate` +
GET) is allowed when `ALLOW_NAVIGATIONS` is enabled. Under LAX,
`ALLOW_SAFE_METHODS` passes all cross-site GET/HEAD requests regardless of mode.

Cross-site form POSTs (`Sec-Fetch-Mode: navigate` + POST) are blocked under all
presets. The navigation exemption only applies to safe methods.

## Common Patterns

**Subdomain setup** (allow requests from other subdomains):

```python
FETCH_METADATA_ALLOWED_SITES = ['same-origin', 'same-site', 'none']
```

**Webhook endpoint exemption:**

```python
FETCH_METADATA_EXEMPT_PATHS = ['/webhooks/']
```

**Report-only rollout** (log violations without blocking, then review logs):

```python
FETCH_METADATA_REPORT_ONLY = True
```

Violations are logged to the `fetch_metadata` logger at WARNING level.

## Further Reading

- [Configuration](docs/configuration.md) - all settings, path exemptions, custom failure views
- [Presets](docs/presets.md) - preset details with request flow traces
- [W3C Fetch Metadata spec](https://www.w3.org/TR/fetch-metadata/) - the underlying browser mechanism
- [web.dev: Protect your resources](https://web.dev/articles/fetch-metadata) - Google's implementation guide

## License

MIT. See [LICENSE](LICENSE).
