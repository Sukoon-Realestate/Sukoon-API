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
    _new_id,
    _resolve_id,
)
from .rental_inventory_parts.normalize_inventory import (
    normalize_inventory,
)
