SECRET_KEY = 'fetch-metadata-test-key'

INSTALLED_APPS = [
    'django.contrib.contenttypes',
    'django.contrib.auth',
    'fetch_metadata',
]

MIDDLEWARE = [
    'django.middleware.common.CommonMiddleware',
    'fetch_metadata.middleware.FetchMetadataMiddleware',
]

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
    }
}

ROOT_URLCONF = 'fetch_metadata.tests.urls'
DEBUG = True
