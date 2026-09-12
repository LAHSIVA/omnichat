"""
Django settings used exclusively by the test suite.

Production security settings remain enabled in config.settings.
Tests use plain HTTP through Django's test client, so HTTPS
redirects must be disabled here.
"""

from .settings import *  # noqa: F401,F403


# ---------------------------------------------------------------------------
# Test environment
# ---------------------------------------------------------------------------

DEBUG = True

# Django's test client uses http://testserver by default.
# Do not redirect test requests to HTTPS.
SECURE_SSL_REDIRECT = False

# Test requests don't need production-only secure cookie behavior.
SESSION_COOKIE_SECURE = False
CSRF_COOKIE_SECURE = False

# Don't enable HSTS in tests.
SECURE_HSTS_SECONDS = 0
SECURE_HSTS_INCLUDE_SUBDOMAINS = False
SECURE_HSTS_PRELOAD = False

# Django's test client uses this host.
ALLOWED_HOSTS = [
    "testserver",
    "localhost",
    "127.0.0.1",
]
