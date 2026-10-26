"""Use the reviewed visit version and a distinct response intention in HTTP tests."""

from uuid import uuid4


def response_body(revision, **values):
    return {"request_key": str(uuid4()), "expected_revision": revision, **values}
