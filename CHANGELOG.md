# Changelog

## 0.1.0 (2026-03-29)

Initial release.

- Resource isolation policy middleware using Sec-Fetch-Site and Sec-Fetch-Mode headers
- Three named presets: DEFAULT, API, STRICT
- Per-view `@fetch_metadata_exempt` and `@fetch_metadata_policy` decorators (work directly on both function-based and class-based views)
- Configurable violation response with debug page (DEBUG mode)
- Custom failure view support via `FETCH_METADATA_FAILURE_VIEW`
- `FetchMetadataTestMixin` for downstream project tests
- Optional Django Debug Toolbar panel
- System checks for common misconfigurations
- Report-only mode for safe rollout
