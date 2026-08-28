"""PIN hashing for employee logins.

PINs are stored as PBKDF2-SHA256 hashes with a per-PIN random salt, so the
plaintext is never written to disk. The stored form is scheme-versioned:

    pbkdf2$sha256$<iterations>$<salt b64>$<hash b64>

Legacy plaintext PINs (no scheme prefix) are detected by ``is_hashed`` so the
startup migration in ``db._migrate`` can upgrade them in place, and
``verify_pin`` still accepts them before that happens.
"""

import base64
import hashlib
import hmac
import os

SCHEME = "pbkdf2"
_ALGO = "sha256"
_ITERATIONS = 100_000


def hash_pin(pin):
    """Return the canonical PBKDF2 digest string for a plaintext PIN."""
    salt = os.urandom(16)
    digest = hashlib.pbkdf2_hmac(
        _ALGO, str(pin).encode(), salt, _ITERATIONS)
    return "$".join([
        SCHEME, _ALGO, str(_ITERATIONS),
        base64.b64encode(salt).decode(),
        base64.b64encode(digest).decode(),
    ])


def is_hashed(stored):
    """True if a stored value uses our hashed scheme (vs legacy plaintext)."""
    parts = str(stored).split("$")
    return len(parts) == 5 and parts[0] == SCHEME


def verify_pin(pin, stored):
    """Constant-time check of a candidate PIN against a stored value."""
    pin = str(pin)
    stored = str(stored)
    if not is_hashed(stored):
        # Legacy plaintext PIN (pre-hashing database) — match directly.
        return hmac.compare_digest(pin, stored)
    _, algo, iters, salt_b64, hash_b64 = stored.split("$")
    digest = hashlib.pbkdf2_hmac(
        algo, pin.encode(), base64.b64decode(salt_b64), int(iters))
    return hmac.compare_digest(digest, base64.b64decode(hash_b64))