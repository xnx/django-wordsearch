"""Settings for the package's own tests, independent of any site."""

SECRET_KEY = "wordsearch-tests"
DEBUG = False
USE_TZ = True
INSTALLED_APPS = [
    "django.contrib.staticfiles",
    "wordsearch",
]
MIDDLEWARE = [
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
]
ROOT_URLCONF = "tests.urls"
DATABASES = {}
TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "APP_DIRS": True,
        "OPTIONS": {
            "context_processors": ["django.template.context_processors.request"]
        },
    }
]
STATIC_URL = "/static/"
