from django.test import SimpleTestCase, override_settings

from fetch_metadata.conf import get_config


class TestGetConfig(SimpleTestCase):
    def test_default_preset_allowed_sites(self):
        # no settings defined: returns DEFAULT preset values
        result = get_config('ALLOWED_SITES')
        self.assertEqual(result, ['same-origin', 'none'])

    def test_default_preset_allow_navigations(self):
        result = get_config('ALLOW_NAVIGATIONS')
        self.assertTrue(result)

    def test_default_preset_fail_open(self):
        result = get_config('FAIL_OPEN')
        self.assertTrue(result)

    def test_default_preset_report_only(self):
        result = get_config('REPORT_ONLY')
        self.assertFalse(result)

    @override_settings(FETCH_METADATA_ALLOWED_SITES=['same-origin', 'same-site', 'none'])
    def test_explicit_setting_overrides_preset(self):
        # explicit FETCH_METADATA_ALLOWED_SITES overrides DEFAULT preset
        result = get_config('ALLOWED_SITES')
        self.assertEqual(result, ['same-origin', 'same-site', 'none'])

    @override_settings(FETCH_METADATA_PRESET='API')
    def test_api_preset(self):
        # API preset: same-origin only, no navigations
        self.assertEqual(get_config('ALLOWED_SITES'), ['same-origin'])
        self.assertFalse(get_config('ALLOW_NAVIGATIONS'))
        self.assertTrue(get_config('FAIL_OPEN'))

    @override_settings(FETCH_METADATA_PRESET='STRICT')
    def test_strict_preset(self):
        # STRICT preset: same-origin only, no navigations, fail-closed
        self.assertEqual(get_config('ALLOWED_SITES'), ['same-origin'])
        self.assertFalse(get_config('ALLOW_NAVIGATIONS'))
        self.assertFalse(get_config('FAIL_OPEN'))

    @override_settings(FETCH_METADATA_PRESET='API', FETCH_METADATA_ALLOWED_SITES=['same-origin', 'none'])
    def test_explicit_setting_overrides_named_preset(self):
        # explicit setting wins over named preset
        result = get_config('ALLOWED_SITES')
        self.assertEqual(result, ['same-origin', 'none'])

    @override_settings(FETCH_METADATA_REPORT_ONLY=False)
    def test_sentinel_distinguishes_false_from_unset(self):
        # explicit False is not the same as unset
        result = get_config('REPORT_ONLY')
        self.assertFalse(result)

    @override_settings(FETCH_METADATA_PRESET='NONEXISTENT')
    def test_invalid_preset_raises_key_error(self):
        # invalid preset name raises KeyError (caught by system check at startup)
        with self.assertRaises(KeyError):
            get_config('ALLOWED_SITES')
