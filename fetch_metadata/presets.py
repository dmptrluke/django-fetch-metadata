PRESETS = {
    'DEFAULT': {
        'ALLOWED_SITES': ['same-origin', 'none'],
        'ALLOW_NAVIGATIONS': True,
        'ALLOW_SAFE_METHODS': False,
        'FAIL_OPEN': True,
        'REPORT_ONLY': False,
        'EXEMPT_PATHS': [],
    },
    'LAX': {
        'ALLOWED_SITES': ['same-origin', 'none'],
        'ALLOW_NAVIGATIONS': True,
        'ALLOW_SAFE_METHODS': True,
        'FAIL_OPEN': True,
        'REPORT_ONLY': False,
        'EXEMPT_PATHS': [],
    },
    'API': {
        'ALLOWED_SITES': ['same-origin'],
        'ALLOW_NAVIGATIONS': False,
        'ALLOW_SAFE_METHODS': False,
        'FAIL_OPEN': True,
        'REPORT_ONLY': False,
        'EXEMPT_PATHS': [],
    },
    'STRICT': {
        'ALLOWED_SITES': ['same-origin'],
        'ALLOW_NAVIGATIONS': False,
        'ALLOW_SAFE_METHODS': False,
        'FAIL_OPEN': False,
        'REPORT_ONLY': False,
        'EXEMPT_PATHS': [],
    },
}
