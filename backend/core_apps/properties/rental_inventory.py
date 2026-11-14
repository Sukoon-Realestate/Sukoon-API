"""Stable public imports for rental inventory.

Implementation modules separate domain responsibilities without changing routes.
"""

import copy
import uuid
from decimal import Decimal, InvalidOperation
from rest_framework.exceptions import ValidationError

from .rental_inventory_parts.inheritable import (
    SCOPES,
    AVAILABILITY,
    INHERITABLE,
)
# Supported private imports stay outside the public star-import surface.
from .rental_inventory_parts.inheritable import (  # noqa: F401
    _new_id,
    _resolve_id,
)
from .rental_inventory_parts.normalize_inventory import (
    normalize_inventory,
)

# Preserve the existing public import surface, including compatibility seams.
__all__ = [
    'copy',
    'uuid',
    'Decimal',
    'InvalidOperation',
    'ValidationError',
    'SCOPES',
    'AVAILABILITY',
    'INHERITABLE',
    'normalize_inventory',
]
