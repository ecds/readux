"""
With these settings, tests run faster.
"""

import fakeredis

from .local import *  # noqa
from .local import env

# Run Celery tasks synchronously through the real task machinery (not a bare
# function call) so on_success/on_failure/retry logic actually executes in
# tests -- unlike this codebase's `if DJANGO_ENV == "test": call_task_fn()`
# pattern, which calls the undecorated function and skips that machinery
# entirely.
CELERY_ALWAYS_EAGER = True
CELERY_EAGER_PROPAGATES_EXCEPTIONS = True

# Swap the real Redis connection for an in-memory fake, so cache.add() (used
# for ingest task locking) is exercised against real atomic SET-NX semantics
# without needing a Redis server in CI. django-redis only import_string()s
# the top-level CONNECTION_POOL_CLASS/REDIS_CLIENT_CLASS options, not nested
# kwargs, so connection_class has to be the actual class, not a dotted path.
CACHES = {
    "default": {
        "BACKEND": "django_redis.cache.RedisCache",
        "LOCATION": "redis://localhost:6379/1",
        "OPTIONS": {
            "CONNECTION_POOL_KWARGS": {"connection_class": fakeredis.FakeConnection},
        },
    }
}

