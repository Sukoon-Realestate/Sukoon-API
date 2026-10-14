"""Stable public imports for lifestyle matching.

Implementation modules separate domain responsibilities without changing routes.
"""

from datetime import time
from rest_framework.exceptions import ValidationError

from .lifestyle_matching_parts.profile_extensions import (
    UNKNOWN,
    profile_extensions,
    match_facts,
)
from .lifestyle_matching_parts.disclosure_scope import (
    disclosure_scope,
)
