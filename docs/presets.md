# Presets

Presets provide named configurations for common deployment patterns. Set with
`FETCH_METADATA_PRESET` in your Django settings.

## DEFAULT

Full resource isolation. Same-origin requests and direct navigations pass.
Cross-site link clicks (navigations via GET/HEAD) are allowed. All other
cross-site requests are blocked, including cross-site `fetch()` GETs, `<script>`
includes, `<img>` loads, and iframe embeds.

```python
ALLOWED_SITES = ['same-origin', 'none']
ALLOW_NAVIGATIONS = True
ALLOW_SAFE_METHODS = False
FAIL_OPEN = True
```

**Request flow examples:**

| Request | Site | Mode | Result |
|---------|------|------|--------|
| Same-origin AJAX POST | `same-origin` | `cors` | Allowed |
| Bookmark / URL bar (GET) | `none` | `navigate` | Allowed |
| Cross-site link click (GET) | `cross-site` | `navigate` | Allowed |
| Cross-site fetch() GET | `cross-site` | `cors` | **Blocked** |
| Cross-site `<script>` GET | `cross-site` | `no-cors` | **Blocked** |
| Cross-site iframe (GET) | `cross-site` | `nested-navigate` | **Blocked** |
| Cross-site form POST | `cross-site` | `navigate` | **Blocked** |
| curl / webhook (no headers) | - | - | Allowed (fail-open) |
| Same-site subdomain fetch() | `same-site` | `cors` | **Blocked** |

**Caveat:** DEFAULT blocks `same-site` requests. If your architecture spans
subdomains (e.g. `api.example.com` calling `app.example.com`), add `same-site`
to your allowed sites:

```python
FETCH_METADATA_ALLOWED_SITES = ['same-origin', 'same-site', 'none']
```

## LAX

CSRF-like protection. All cross-site GET/HEAD requests pass (including
`fetch()`, `<script>`, `<img>`, iframes). Only cross-site state-changing
requests (POST, PUT, DELETE, PATCH) are blocked.

```python
ALLOWED_SITES = ['same-origin', 'none']
ALLOW_NAVIGATIONS = True
ALLOW_SAFE_METHODS = True
FAIL_OPEN = True
```

**Request flow examples:**

| Request | Site | Mode | Result |
|---------|------|------|--------|
| Same-origin AJAX POST | `same-origin` | `cors` | Allowed |
| Cross-site link click (GET) | `cross-site` | `navigate` | Allowed |
| Cross-site fetch() GET | `cross-site` | `cors` | Allowed |
| Cross-site `<script>` GET | `cross-site` | `no-cors` | Allowed |
| Cross-site iframe (GET) | `cross-site` | `nested-navigate` | Allowed |
| Cross-site form POST | `cross-site` | `navigate` | **Blocked** |
| Cross-site fetch() POST | `cross-site` | `cors` | **Blocked** |
| curl / webhook (no headers) | - | - | Allowed (fail-open) |

## API

API endpoint. Same-origin only, no navigations. Intended for endpoints behind
token or session auth that should only be called by your own frontend.
Missing headers pass through for server-to-server compatibility.

```python
ALLOWED_SITES = ['same-origin']
ALLOW_NAVIGATIONS = False
ALLOW_SAFE_METHODS = False
FAIL_OPEN = True
```

**Request flow examples:**

| Request | Site | Mode | Result |
|---------|------|------|--------|
| Same-origin AJAX POST | `same-origin` | `cors` | Allowed |
| Cross-site link click (GET) | `cross-site` | `navigate` | **Blocked** |
| Cross-site fetch() | `cross-site` | `cors` | **Blocked** |
| Direct navigation (GET) | `none` | `navigate` | **Blocked** |
| Server-to-server (no headers) | - | - | Allowed (fail-open) |

## STRICT

Locked-down browser-only. Same-origin only, no navigations, missing headers
blocked. Non-browser clients need per-view exemption (`@fetch_metadata_exempt`)
or path exemption.

```python
ALLOWED_SITES = ['same-origin']
ALLOW_NAVIGATIONS = False
FAIL_OPEN = False
```

**Request flow examples:**

| Request | Site | Mode | Result |
|---------|------|------|--------|
| Same-origin AJAX POST | `same-origin` | `cors` | Allowed |
| Cross-site anything | `cross-site` | any | **Blocked** |
| curl / webhook (no headers) | - | - | **Blocked** |
| Health check (no headers) | - | - | **Blocked** |

Use for admin panels and internal tools where all legitimate callers are
browsers you control. Exempt health check and monitoring endpoints:

```python
FETCH_METADATA_PRESET = 'STRICT'
FETCH_METADATA_EXEMPT_PATHS = ['/health/']
```

## Overriding Preset Values

Explicit settings override individual preset values without replacing the
whole preset:

```python
# Start with API preset, but also allow 'none' (direct navigation)
FETCH_METADATA_PRESET = 'API'
FETCH_METADATA_ALLOWED_SITES = ['same-origin', 'none']
```

Per-view `@fetch_metadata_policy` overrides policy settings for that view
only. Deployment settings (`REPORT_ONLY`, `EXEMPT_PATHS`) are always global.
