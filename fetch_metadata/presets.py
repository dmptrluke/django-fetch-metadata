PRESETS = {
    'DEFAULT': {
        'ALLOWED_SITES': ['same-origin', 'none'],
        'ALLOW_NAVIGATIONS': True,
        'FAIL_OPEN': True,
        'REPORT_ONLY': False,
        'EXEMPT_PATHS': [],
    },
    'API': {
        'ALLOWED_SITES': ['same-origin'],
        'ALLOW_NAVIGATIONS': False,
        'FAIL_OPEN': True,
        'REPORT_ONLY': False,
        'EXEMPT_PATHS': [],
    },
    'STRICT': {
        'ALLOWED_SITES': ['same-origin'],
        'ALLOW_NAVIGATIONS': False,
        'FAIL_OPEN': False,
        'REPORT_ONLY': False,
        'EXEMPT_PATHS': [],
    },
}
