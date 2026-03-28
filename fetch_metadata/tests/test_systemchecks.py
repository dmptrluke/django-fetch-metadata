from django.test import SimpleTestCase, override_settings

from fetch_metadata.systemchecks import check_settings


class TestSystemChecks(SimpleTestCase):
    def test_w001_middleware_missing(self):
        # W001 fires when middleware is not in MIDDLEWARE
        with self.settings(MIDDLEWARE=[]):
            errors = check_settings()
        warnings = [e for e in errors if e.id == 'fetch_metadata.W001']
        self.assertEqual(len(warnings), 1)

    def test_no_w001_when_middleware_present(self):
        # no W001 when middleware is properly configured
        errors = check_settings()
        warnings = [e for e in errors if e.id == 'fetch_metadata.W001']
        self.assertEqual(len(warnings), 0)

    @override_settings(FETCH_METADATA_REPORT_ONLY=True, DEBUG=False)
    def test_w002_report_only_non_debug(self):
        # W002 fires when report-only is enabled in non-debug mode
        errors = check_settings()
        warnings = [e for e in errors if e.id == 'fetch_metadata.W002']
        self.assertEqual(len(warnings), 1)

    @override_settings(FETCH_METADATA_REPORT_ONLY=True, DEBUG=True)
    def test_no_w002_when_debug(self):
        # no W002 when DEBUG=True (development)
        errors = check_settings()
        warnings = [e for e in errors if e.id == 'fetch_metadata.W002']
        self.assertEqual(len(warnings), 0)

    @override_settings(FETCH_METADATA_PRESET='NONEXISTENT')
    def test_e001_invalid_preset(self):
        # E001 fires for unknown preset name
        errors = check_settings()
        check_errors = [e for e in errors if e.id == 'fetch_metadata.E001']
        self.assertEqual(len(check_errors), 1)
        self.assertIn('NONEXISTENT', check_errors[0].msg)

    @override_settings(FETCH_METADATA_ALLOWED_SITES='same-origin')
    def test_e002_string_allowed_sites(self):
        # E002 fires when ALLOWED_SITES is a string instead of list
        errors = check_settings()
        check_errors = [e for e in errors if e.id == 'fetch_metadata.E002']
        self.assertEqual(len(check_errors), 1)

    @override_settings(FETCH_METADATA_FAILURE_VIEW='nonexistent.module.view')
    def test_e003_failure_view_not_importable(self):
        # E003 fires when failure view cannot be imported
        errors = check_settings()
        check_errors = [e for e in errors if e.id == 'fetch_metadata.E003']
        self.assertEqual(len(check_errors), 1)

    def test_no_errors_when_properly_configured(self):
        # no errors with default test settings
        errors = check_settings()
        actual_errors = [e for e in errors if e.id.startswith('fetch_metadata.E')]
        self.assertEqual(len(actual_errors), 0)

    @override_settings(FETCH_METADATA_PRESET='API')
    def test_no_e001_when_preset_valid(self):
        # E001 does not fire for a valid preset name
        errors = check_settings()
        check_errors = [e for e in errors if e.id == 'fetch_metadata.E001']
        self.assertEqual(len(check_errors), 0)

    @override_settings(FETCH_METADATA_ALLOWED_SITES=['same-origin', 'none'])
    def test_no_e002_when_allowed_sites_is_list(self):
        # E002 does not fire when ALLOWED_SITES is a list
        errors = check_settings()
        check_errors = [e for e in errors if e.id == 'fetch_metadata.E002']
        self.assertEqual(len(check_errors), 0)

    @override_settings(FETCH_METADATA_FAILURE_VIEW='fetch_metadata.tests.urls.failure_view')
    def test_no_e003_when_failure_view_importable(self):
        # E003 does not fire when failure view can be imported
        errors = check_settings()
        check_errors = [e for e in errors if e.id == 'fetch_metadata.E003']
        self.assertEqual(len(check_errors), 0)

    @override_settings(FETCH_METADATA_PRESET='NONEXISTENT')
    def test_e001_returns_early(self):
        # E001 returns early, so W002/E002/E003 don't run with broken preset
        errors = check_settings()
        # only E001 (test settings have middleware, so no W001)
        self.assertEqual(len(errors), 1)
        self.assertEqual(errors[0].id, 'fetch_metadata.E001')
