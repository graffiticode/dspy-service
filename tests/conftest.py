"""Test configuration.

The service refuses protected routes when no INTERNAL_API_KEY is configured. The endpoint tests exercise
behaviour, not auth, so they run in explicit local-development mode; tests/test_auth.py covers the auth paths.
"""

import os

os.environ.setdefault("ALLOW_UNAUTHENTICATED_DEV", "1")
