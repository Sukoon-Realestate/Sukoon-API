"""Local-only Apple signing key, used to drive Apple login without a real device.

Both sides of the loop read the key from the SAME PEM file:
  - `mint_apple_token` signs an identity token with the private key
  - `_get_apple_jwks` publishes the matching public key as if it were Apple's JWKS

# ! Development only. If a server ever loads this key it will accept forged Apple
#   logins for any email. It is activated solely by APPLE_DEV_PRIVATE_KEY_PATH,
#   which must never be set on a deployed host.
"""

import json
import os

from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric import rsa

# * Must match the `kid` stamped into minted tokens so JWKS lookup succeeds
DEV_KID = "local-dev-apple-key"
APPLE_ISSUER = "https://appleid.apple.com"

_RSA_PUBLIC_EXPONENT = 65537
_RSA_KEY_SIZE = 2048


def load_dev_key(path: str):
    """Return the dev RSA private key, or None if the PEM does not exist.

    # ! Never generates a key. The server MUST use this rather than
    #   `load_or_create_dev_key` — auto-generating on a host where the env var leaked
    #   would silently publish a forgeable key as Apple's and fail OPEN.
    """
    if not os.path.exists(path):
        return None
    with open(path, "rb") as handle:
        return serialization.load_pem_private_key(handle.read(), password=None)


def load_or_create_dev_key(path: str):
    """Return the dev RSA private key, generating and persisting it on first use.

    # ! Only `mint_apple_token` may call this — it is the one place creating a key is intended.
    """
    existing = load_dev_key(path)
    if existing is not None:
        return existing

    private_key = rsa.generate_private_key(
        public_exponent=_RSA_PUBLIC_EXPONENT,
        key_size=_RSA_KEY_SIZE,
    )
    pem = private_key.private_bytes(
        encoding=serialization.Encoding.PEM,
        format=serialization.PrivateFormat.PKCS8,
        encryption_algorithm=serialization.NoEncryption(),
    )
    directory = os.path.dirname(path)
    if directory:
        os.makedirs(directory, exist_ok=True)
    with open(path, "wb") as handle:
        handle.write(pem)
    # ? Key can forge logins on any server trusting it — keep it owner-readable only
    os.chmod(path, 0o600)
    return private_key


def build_dev_jwks(private_key) -> dict:
    """Render the public key as a JWKS document matching Apple's /auth/keys shape."""
    from jwt.algorithms import RSAAlgorithm

    jwk = json.loads(RSAAlgorithm.to_jwk(private_key.public_key()))
    jwk.update({"kid": DEV_KID, "alg": "RS256", "use": "sig"})
    return {"keys": [jwk]}
